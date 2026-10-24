"""Draft 2025 APCM adoption forecast and readiness score (NOT frozen).

Target (assumptions log A19): a primary care practice has at least one visible APCM
row (G0556-G0558) in the 2025 Physician & Other Practitioners file. That file is not
yet published, so no APCM outcome can be used for training. The model is trained on the
closest real launch: G2211, a primary care code introduced in January 2024.

  Model A (primary):  2023 practice profile -> visible G2211 billing in 2024
  Model B (check):    2023 profile -> first visible CCM or PCM billing in 2024,
                      among practices with neither in 2023

Each model is an unpenalised logistic regression on standardised features (A20). The
2024 profile is then scored with model A; the readiness score is the practice's
percentile (0-100) of that predicted probability. Probabilities are scaled to G2211
uptake, not APCM uptake, so only the ranking is meaningful.

Outputs go to pipeline_output/forecast/ as DRAFT files. Freezing them with
scripts/freeze_forecast.py is a one-way step and needs Anandi's sign-off.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pipeline_output" / "forecast"
OUT.mkdir(parents=True, exist_ok=True)
db = duckdb.connect(str(ROOT / "apcm_opportunity.duckdb"), read_only=True)

FEATURES = ["log_panel", "log_clinicians", "physician_share", "dual_share", "avg_hcc_risk_score",
            "metro_share", "has_ccm", "has_pcm", "has_tcm", "has_bhi_or_cocm", "has_rpm", "has_acp",
            "awv_clinician_share", "log_office_em_per_bene"]
IMPUTED = ["dual_share", "avg_hcc_risk_score", "metro_share"]


def frame(year: int) -> pd.DataFrame:
    d = db.execute("select * from int_practice_year where service_year = ?", [year]).df()
    d["log_panel"] = np.log1p(d["patient_panel_proxy"].fillna(0))
    d["log_clinicians"] = np.log1p(d["pcp_clinicians"])
    d["log_office_em_per_bene"] = np.log1p(d["office_em_per_bene"].fillna(0))
    for b in ["has_ccm", "has_pcm", "has_tcm", "has_bhi_or_cocm", "has_rpm", "has_acp",
              "has_established_care_mgmt", "has_g2211", "has_apcm"]:
        d[b] = d[b].fillna(False).astype(int)
    return d


def prep(d: pd.DataFrame, feats: list[str], ref: dict | None = None):
    """Median-impute (with missing flags) and standardise using training statistics."""
    x = d[feats].astype(float).copy()
    if ref is None:
        ref = {"median": x.median().to_dict(), "mean": {}, "sd": {}}
    for c in IMPUTED:
        if c in x:
            x[f"{c}_missing"] = x[c].isna().astype(float)
            x[c] = x[c].fillna(ref["median"][c])
    if not ref["mean"]:
        sd = x.std()
        ref["dropped_constant"] = sd.index[~(sd > 0)].tolist()  # constant columns make the fit singular
        x = x.loc[:, sd > 0]
        ref["mean"] = x.mean().to_dict()
        ref["sd"] = x.std().to_dict()
    x = x[list(ref["mean"])]
    x = (x - pd.Series(ref["mean"])) / pd.Series(ref["sd"])
    return sm.add_constant(x, has_constant="add"), ref


def auroc(y: np.ndarray, p: np.ndarray) -> float:
    r = pd.Series(p).rank().to_numpy()
    n1 = y.sum(); n0 = len(y) - n1
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def fit(train: pd.DataFrame, label: str, feats: list[str], seed: int = 20261024) -> dict:
    y = train[label].to_numpy()
    folds = np.random.default_rng(seed).integers(0, 5, len(train))
    cv_p = np.zeros(len(train))
    for k in range(5):
        tr, te = folds != k, folds == k
        xtr, ref = prep(train[tr], feats)
        xte, _ = prep(train[te], feats, ref)
        cv_p[te] = sm.Logit(y[tr], xtr).fit(disp=0, maxiter=200).predict(xte)
    x, ref = prep(train, feats)
    model = sm.Logit(y, x).fit(disp=0, maxiter=200)
    return {
        "model": model, "ref": ref, "n": int(len(train)), "events": int(y.sum()),
        "prevalence": float(y.mean()), "cv_auroc": auroc(y, cv_p),
        "cv_brier": float(np.mean((cv_p - y) ** 2)), "brier_null": float(y.mean() * (1 - y.mean())),
        "coef": {k: {"beta_per_sd": float(model.params[k]), "odds_ratio_per_sd": float(np.exp(model.params[k])),
                     "p_value": float(model.pvalues[k])} for k in model.params.index},
    }


f23, f24 = frame(2023), frame(2024)
lab = f24[["practice_id", "has_g2211", "has_established_care_mgmt"]].rename(
    columns={"has_g2211": "y_g2211_2024", "has_established_care_mgmt": "y_cm_2024"})
train = f23.merge(lab, on="practice_id", how="inner")

model_a = fit(train, "y_g2211_2024", FEATURES)
feats_b = [f for f in FEATURES if f not in ("has_ccm", "has_pcm")]
train_b = train[train["has_established_care_mgmt"] == 0]
model_b = fit(train_b, "y_cm_2024", feats_b)

score = f24[["practice_id"]].copy()
xa, _ = prep(f24, FEATURES, model_a["ref"])
xb, _ = prep(f24, feats_b, model_b["ref"])
score["p_model_a"] = model_a["model"].predict(xa)
score["p_model_b"] = model_b["model"].predict(xb)
score["readiness_score"] = (score["p_model_a"].rank(pct=True) * 100).round(1)
score["readiness_decile"] = np.ceil(score["readiness_score"] / 10).clip(1, 10).astype(int)
score["observed_g2211_2024"] = f24["has_g2211"].to_numpy()
spearman = float(score["p_model_a"].rank().corr(score["p_model_b"].rank()))

practice = db.execute("""select practice_id, state, rurality, county_geographic_pc_hpsa, dual_share,
    est_qmb_patients, patient_panel_proxy, readiness_tier, apcm_allowed_base_scenario from mart_practice""").df()
scored = score.merge(practice, on="practice_id", how="left")
scored.round(5).to_csv(OUT / "draft_2025_apcm_predictions.csv.gz", index=False, compression="gzip")

deciles = scored.groupby("readiness_decile").agg(
    practices=("practice_id", "size"), mean_p_model_a=("p_model_a", "mean"),
    observed_g2211_2024=("observed_g2211_2024", "mean"), patient_panel_proxy=("patient_panel_proxy", "sum"),
    est_qmb_patients=("est_qmb_patients", "sum"), mean_dual_share=("dual_share", "mean"),
    apcm_allowed_base_scenario=("apcm_allowed_base_scenario", "sum")).reset_index()
deciles.to_csv(OUT / "readiness_deciles.csv", index=False, float_format="%.6g")

# Where QMB patients sit relative to readiness: the equity question in one table
qmb_by_decile = deciles[["readiness_decile", "est_qmb_patients", "patient_panel_proxy"]].copy()
qmb_by_decile["qmb_share_of_all_qmb"] = qmb_by_decile["est_qmb_patients"] / qmb_by_decile["est_qmb_patients"].sum()
qmb_by_decile["panel_share_of_all"] = qmb_by_decile["patient_panel_proxy"] / qmb_by_decile["patient_panel_proxy"].sum()
qmb_by_decile.to_csv(OUT / "qmb_by_readiness_decile.csv", index=False, float_format="%.6g")


def card(m: dict) -> dict:
    return {k: v for k, v in m.items() if k not in ("model", "ref")} | {"standardisation": m["ref"]}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifests = {p.name: sha(p) for p in sorted((ROOT / "pipeline_output" / "manifests").glob("*.json"))}
commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
model_card = {
    "status": "DRAFT, not frozen. Freeze only with Anandi's approval (scripts/freeze_forecast.py).",
    "target": "Practice has >=1 visible APCM (G0556-G0558) row in the 2025 CMS Physician & Other "
              "Practitioners by Provider and Service file (clinician-code rows with 11+ beneficiaries).",
    "outcome_release": "Expected with the 2025 service-year file (CMS has published each year's file about "
                       "17 months after year end; 2024 data appeared May 2026).",
    "practice_definition": "Group practice (org PAC ID) from the current Doctors and Clinicians file, else solo NPI.",
    "training_design": "Launch analog. Model A: 2023 features -> G2211 billing in 2024. Model B: 2023 features "
                       "-> new CCM/PCM billing in 2024 among practices with neither in 2023.",
    "scoring": "2024 features scored with model A; readiness_score = percentile of predicted probability.",
    "model_a_g2211_launch": card(model_a),
    "model_b_new_care_management": card(model_b),
    "rank_agreement_spearman_a_vs_b_2024": spearman,
    "evaluation_plan": "When 2025 data publish: AUROC, average precision, Brier score, calibration by decile, "
                       "and uptake by decile within dual-share quintiles. Compare against the naive rule "
                       "'practice billed CCM or PCM in 2024'.",
    "source_manifest_sha256": manifests,
    "repository_commit": commit,
}
(OUT / "model_card_draft.json").write_text(json.dumps(model_card, indent=2, default=str))
print(f"forecast: A auroc={model_a['cv_auroc']:.3f} n={model_a['n']}, B auroc={model_b['cv_auroc']:.3f} "
      f"n={model_b['n']}, spearman={spearman:.3f}, scored={len(scored)}")
