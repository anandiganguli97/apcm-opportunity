"""Build the static dashboard from committed pipeline outputs.

Reads pipeline_output/results and pipeline_output/forecast, inlines the aggregates
into dashboard/template.html and writes dashboard/index.html, a single file with no
data requests (it works from GitHub Pages or straight off disk).

    python pipeline/build_dashboard.py                 # dashboard/index.html
    python pipeline/build_dashboard.py --fragment PATH # page body only, for embedding
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "pipeline_output" / "results"
FC = ROOT / "pipeline_output" / "forecast"
TEMPLATE = ROOT / "dashboard" / "template.html"
STATES = set("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM "
             "NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split())


def rows(frame: pd.DataFrame) -> list[dict]:
    out = frame.to_dict(orient="records")
    return [{k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in r.items()} for r in out]


def build() -> dict:
    trend = pd.read_csv(RES / "national_trend.csv")
    equity = pd.read_csv(RES / "equity.csv")
    opp = pd.read_csv(RES / "apcm_opportunity_national.csv").set_index("scenario")
    tiers = pd.read_csv(RES / "readiness_tiers.csv")
    tq = pd.read_csv(RES / "readiness_by_dual_quintile.csv")
    ccm = pd.read_csv(RES / "ccm_vs_apcm_summary.csv").iloc[0]
    fee = pd.read_csv(RES / "fee_schedule_2026.csv")
    sup = pd.read_csv(RES / "suppression_by_family.csv")
    states = pd.read_csv(RES / "state_summary.csv")
    dec = pd.read_csv(FC / "qmb_by_readiness_decile.csv").merge(
        pd.read_csv(FC / "readiness_deciles.csv")[["readiness_decile", "practices", "mean_dual_share", "mean_p_model_a"]],
        on="readiness_decile")
    card = json.loads((FC / "model_card_draft.json").read_text())
    manifests = {p.stem: json.loads(p.read_text()) for p in sorted((ROOT / "pipeline_output" / "manifests").glob("*.json"))}

    rate = {r.hcpcs: r.national_nonfac_amount for r in fee[fee.cf_type == "nonqpp"].itertuples()}
    year = int(trend.service_year.max())
    last = trend[trend.service_year == year].iloc[0]
    eq = equity[equity.dimension != "All primary care clinicians"]
    eq = eq[~((eq.grp == "Unknown") & (eq.dimension.str.startswith("Rurality")))]

    tq = tq.assign(tier=tq.readiness_tier.str[0].astype(int))
    qmb_tq = []
    for q, g in tq.groupby("dual_quintile"):
        total = g.est_qmb_patients.sum()
        qmb_tq.append({"quintile": int(q), "min_dual": float(g.min_dual_share.min()), "max_dual": float(g.max_dual_share.max()),
                       "qmb_total": float(total), "practices": int(g.practices.sum()),
                       "shares": [float(g.loc[g.tier == t, "est_qmb_patients"].sum() / total) for t in range(4)]})

    sup24 = sup[(sup.service_year == year) & sup.family.notna()].sort_values("invisible_service_share", ascending=False)
    fam_names = {"ACP": "Advance care planning", "AWV": "Annual wellness visit", "BHI": "Behavioral health integration",
                 "CCM": "Chronic care management", "COCM": "Collaborative care", "COMPLEXITY_ADDON": "Visit complexity add-on (G2211)",
                 "PCM": "Principal care management", "RPM": "Remote monitoring", "SDOH_NAVIGATION": "Social needs and navigation",
                 "TCM": "Transitional care management", "OFFICE_EM": "Office visits", "APCM": "APCM",
                 "NURSING_FACILITY": "Nursing facility visits"}

    mup_files = [m for m in manifests.get("mup", []) if m.get("service_year") == year]
    return {
        "year": year,
        "built_from_commit": card.get("repository_commit"),
        "trend": rows(trend),
        "headline": {
            "clinicians": int(last.pcp_clinicians), "share_ccm_or_pcm": float(last.share_billing_ccm_or_pcm),
            "share_awv": float(last.share_billing_awv), "share_g2211": float(last.share_billing_g2211),
            "ffs_benes": float(opp.loc["base", "ffs_benes"]), "qmb_share": float(opp.loc["base", "qmb_share"]),
        },
        "opportunity": {s: {k: float(opp.loc[s, k]) for k in ["allowed_scenario", "allowed_full_capture", "patient_coinsurance_scenario",
                                                              "capture_rate", "consent_rate", "share_2plus_qmb", "share_2plus_non_qmb"]}
                        for s in ["low", "base", "high"]},
        "rates": {c: rate.get(c) for c in ["G0556", "G0557", "G0558", "99490", "99439", "99491", "99487", "99424", "99426"]},
        "equity": rows(eq[["dimension", "grp", "clinicians", "mean_dual_share", "clinician_share_ccm_or_pcm",
                           "dual_patient_share_with_ccm_or_pcm", "nondual_patient_share_with_ccm_or_pcm",
                           "est_qmb_patient_share_with_ccm_or_pcm"]]),
        "tiers": rows(tiers),
        "qmb_by_tier_quintile": qmb_tq,
        "ccm_vs_apcm": {k: float(v) for k, v in ccm.items()},
        "deciles": rows(dec),
        "forecast": {"a": {k: card["model_a_g2211_launch"][k] for k in ["n", "events", "prevalence", "cv_auroc", "cv_brier", "brier_null"]},
                     "b": {k: card["model_b_new_care_management"][k] for k in ["n", "events", "prevalence", "cv_auroc", "cv_brier", "brier_null"]},
                     "spearman": card["rank_agreement_spearman_a_vs_b_2024"],
                     "odds": {m: {k: v["odds_ratio_per_sd"] for k, v in card[key]["coef"].items() if k != "const"}
                              for m, key in [("a", "model_a_g2211_launch"), ("b", "model_b_new_care_management")]}},
        "suppression": [{"family": fam_names.get(r.family, r.family), "code_family": r.family,
                         "national": float(r.national_services), "visible": float(r.visible_services),
                         "invisible_share": float(r.invisible_service_share)} for r in sup24.itertuples()],
        "states": rows(states[states.state.isin(STATES)][["state", "clinicians", "share_ccm_or_pcm", "share_tcm", "share_awv",
                                                          "dual_share", "est_qmb_patients", "practices", "apcm_allowed_base_scenario"]]),
        "sources": [{"file": m.get("file"), "url": m.get("url"), "retrieved_utc": m.get("retrieved_utc"), "sha256": m.get("sha256")}
                    for m in mup_files + manifests.get("reference", []) + manifests.get("pfs", [])],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragment", type=Path, help="write the page body only (no doctype/head) to this path")
    a = ap.parse_args()
    data = json.dumps(build(), separators=(",", ":"), default=str).replace("</", "<\\/")
    body = TEMPLATE.read_text().replace("/*__DATA__*/null", data)
    if a.fragment:
        a.fragment.write_text(body)
        print(f"dashboard fragment -> {a.fragment}")
        return
    page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            "<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
            "body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n"
            + body + "\n</body>\n</html>\n")
    out = ROOT / "dashboard" / "index.html"
    out.write_text(page)
    print(f"dashboard -> {out} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
