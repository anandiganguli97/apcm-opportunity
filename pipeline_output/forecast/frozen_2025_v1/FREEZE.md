# Frozen forecast: 2025 APCM uptake, version 1

**Frozen at:** 2026-10-25T04:35:06Z, before CMS published 2025 service-year data.

## What is predicted

**Target:** a primary care practice has at least one visible APCM row (HCPCS G0556, G0557 or G0558) in the CMS Medicare Physician & Other Practitioners by Provider and Service file for service year 2025 (clinician-code rows with 11 or more beneficiaries), counting any clinician linked to the practice.

**Units:** 51,451 practices (Org PAC ID from the CMS Doctors and Clinicians file, or a solo NPI) with primary care clinicians in service year 2024.

**Prediction:** `p_model_a`, the probability from the primary model, and `readiness_score`, its percentile (0 to 100). Probabilities are scaled to G2211 uptake, so the evaluation is about ranking, not calibration to the APCM rate.

## How it was made

- **Primary model (A):** unpenalised logistic regression trained on 2023 practice profiles to predict visible G2211 billing in 2024 (the code's launch year). n = 47,564 practices, 11,623 adopters; 5-fold cross-validated AUROC 0.800, Brier 0.1391 (constant-guess Brier 0.1847).
- **Check model (B):** same method, predicting first visible CCM or PCM billing in 2024 among practices with neither in 2023. n = 42,386, 1,228 adopters; AUROC 0.742. Rank agreement with A on 2024 profiles: Spearman 0.727.
- **Scoring data:** 2024 practice profiles. Features, coefficients and standardisation are in `model_card.json`.
- **Code and data version:** repository commit `b678262891fa7f581e488173e6945788cec677e2` (pipeline run 40155795020). Source data: CMS service years 2019 to 2024, retrieved 2026-10-24; source manifest hashes below.

## How it will be scored

When CMS publishes the 2025 service-year file, the same pipeline builds the outcome for every practice in the frozen file, then reports:

1. AUROC and average precision of `p_model_a` (and of `p_model_b` as a comparison).
2. Uptake rate by readiness decile.
3. Uptake by decile within dual-eligible-share fifths, to test whether practices with the most QMB patients adopt more slowly at the same readiness.
4. A naive baseline: "the practice billed CCM or PCM in 2024".

Practices are matched by `practice_id`. Those that no longer appear in 2025 are reported separately, not counted as non-adopters. Results will be published next to this file, whatever they show.

## Integrity

| File | SHA-256 |
|---|---|
| `apcm_2025_predictions.csv.gz` | `986b088637ff85a752544526dd0ba4341f025e856b3be189ad9d9ca2651388ba` |
| `model_card.json` | `55b882cd99f0f2419e565574652b1be1d8c49570140a6d1578e15834618ff54a` |
| source manifest `mup.json` | `a38d47ee683af1c3ccf6c9af26f6b4f048058f49adb809d34294c69b6edeb208` |
| source manifest `pfs.json` | `7658998edaa1a82e67f9066ab7d71c0c36c725ec52afc6ccdf8b8179b3a874ae` |
| source manifest `reference.json` | `447885d39d5cf36e512647de549a3cfcb020b66342a55f1e49f81a87edb5b5b0` |

The freeze script refuses to overwrite an existing freeze. This commit is also tagged `forecast-2025-v1`, and GitHub records the push time. `model_card.json` keeps the "DRAFT" status label it had when it was frozen; this record is what makes it final.
