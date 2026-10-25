# Data dictionary

Fields in the files the app, the report and Tableau users read. All live in `pipeline_output/` and are aggregate or public-provider level; none contain names, addresses or patient-level data. Methods are in [`methods.md`](methods.md).

## Practice extract (`results/practice_extract_tableau.csv.gz`, one row per practice, 2024)

| Field | Meaning | Caveat |
|---|---|---|
| `practice_id` | Org PAC ID from CMS Doctors and Clinicians, or `npi:<NPI>` for a solo clinician | Current snapshot applied to 2024 |
| `practice_name` | Organization name from the same file | Blank for solo clinicians |
| `state`, `county_fips`, `rurality` | From the practice's largest clinician; rurality from RUCA | Clinician address, not a service area |
| `county_geographic_pc_hpsa` | County has a designated geographic primary care HPSA | Partial-county designations mark the whole county |
| `svi_overall` | CDC/ATSDR SVI 2022 county percentile | Ecological |
| `pcp_clinicians`, `pcp_physicians` | Primary care clinicians in the practice, and physicians among them | Primary care definition in `seeds/primary_care_specialties.csv` |
| `patient_panel_proxy` | Medicare patients summed across the practice's clinicians | Counts patients who see several clinicians more than once |
| `dual_patients`, `dual_share` | Dual-eligible patients and share | Only clinicians with a reported dual count |
| `est_qmb_patients` | Duals times the county QMB share of duals | Estimate; no public file flags QMBs per clinician |
| `avg_hcc_risk_score` | Patient-weighted HCC risk score | |
| `readiness_tier` | 0 none, 1 visit-based only, 2 CCM or PCM, 3 multi-service | Billing shows a workflow exists, not APCM compliance |
| `has_ccm` ... `has_g2211` | Visible 2024 billing of each service family | False can mean fewer than 11 patients |
| `ccm_patient_months` | First-unit monthly CCM/PCM services | |
| `care_mgmt_allowed_visible` | Visible care management allowed dollars | Suppressed rows excluded |
| `apcm_allowed_full_capture_base`, `apcm_allowed_base_scenario` | Annual APCM allowed amount at 2026 rates, before and after base capture and consent | Scenario, not a forecast |

## Readiness score (`forecast/draft_2025_apcm_predictions.csv.gz`)

| Field | Meaning |
|---|---|
| `p_model_a`, `p_model_b` | Predicted probability from the G2211-launch model and the new-care-management check model |
| `readiness_score` | Percentile (0 to 100) of `p_model_a` across practices |
| `readiness_decile` | 1 (least likely to adopt first) to 10 |
| `observed_g2211_2024` | Whether the practice billed G2211 in 2024 (the training event) |

Probabilities are scaled to G2211 uptake, so only the ranking carries over to APCM. Draft until frozen.

## NPI lookup (`results/npi_practice_lookup.csv.gz`)

`npi`, `practice_id`, `provider_type`, `role` (physician or NP/PA), `state` for 2024 primary care clinicians. NPIs are public identifiers.

## Aggregate results (`results/*.csv`)

| File | Grain | Key fields |
|---|---|---|
| `national_trend.csv` | Service year | Clinician counts; share billing each service family; CCM patient-months per 100 patients |
| `equity.csv` | Dimension and group | Share of clinicians billing CCM/PCM; share of dual, other and QMB patients whose clinician bills it |
| `readiness_tiers.csv`, `readiness_by_dual_quintile.csv` | Tier (and dual-share fifth) | Practices, clinicians, patients, estimated QMB patients, base-scenario dollars |
| `state_summary.csv` | State | Clinician and practice shares, dual share, QMB estimates, base-scenario dollars |
| `ccm_vs_apcm_summary.csv` | National | Median CCM months and revenue per patient; G0557 comparisons |
| `apcm_opportunity_national.csv` | Scenario | Inputs, patient-months by level, allowed amounts, coinsurance |
| `fee_schedule_2026.csv` | Code and conversion factor | RVUs and national amounts |
| `suppression_by_code.csv`, `suppression_by_family.csv` | Code or family and year | National vs visible services; hidden share |

## Reference outputs (`references/`)

Federal Register APCM excerpts with page tags, the CMS payment amount check (summary and by locality), CCW condition text, CMS file documentation excerpts and a manifest of every document fetched.
