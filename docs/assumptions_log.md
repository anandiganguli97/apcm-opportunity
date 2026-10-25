# Assumptions log

**Snapshot:** 2026-10-24. Every modeled input in the project is listed here. Anything not listed comes straight from a source file. Changes go through version control with a reason.

## Definitions

| ID | Assumption | Value used | Alternative worth testing | Why it matters |
|---|---|---|---|---|
| A01 | Primary care clinician | FM, IM, GP, geriatrics physicians; NPs and PAs only in years with a visible wellness visit row | Include all NPs/PAs; require office E/M volume | Sets the denominator for every readiness share |
| A02 | Practice | Most-listed Org PAC ID in the current Doctors and Clinicians file; else solo NPI | TIN-level grouping; health-system rollup | Large multi-site groups collapse into one practice and score as ready if any site bills |
| A03 | Visible billing | One clinician-code row (11+ beneficiaries) | Minimum volume threshold | Small practices with real but low-volume billing look unready (see suppression in the validity report) |
| A04 | Readiness tiers | Rules in `docs/methods.md` | Weighted index | Proxy for APCM workflows, not a check of APCM requirements |
| A05 | QMB patients | Clinician duals times county QMB share of duals (state ratio under 100 county duals) | Use state ratio everywhere | Drives G0558 volume and every QMB equity result |
| A06 | Geography | Clinician ZIP to the county with most of the ZCTA's land area | Population-weighted ZIP-county crosswalk | Assigns HPSA, SVI and QMB ratio |
| A07 | Shortage area | County contains at least one designated geographic or high-needs geographic primary care HPSA | Population or facility HPSAs; HPSA score threshold | Partial-county HPSAs mark the whole county |

## Payment

| ID | Assumption | Value used | Source / note |
|---|---|---|---|
| A10 | Fee schedule | CY2026 PFS RVU file, release D (Oct 2026) | `pipeline_output/manifests/pfs.json` |
| A11 | Conversion factor | Non-qualifying APM, $33.4009 | Qualifying APM CF is $33.5675; amounts differ by under 0.5% |
| A12 | Geography | National amounts, no GPCI | GPCIs are staged (`pfs_gpci.parquet`) for a later locality version |
| A13 | Setting | Non-facility amount | Facility amounts are lower (G0557 $33.73) |
| A14 | Coinsurance | 20% of allowed for non-QMB patients, 0% for QMBs | Supplemental coverage pays much of the 20% for many patients |

## Scenario inputs (`seeds/apcm_scenarios.csv`)

These are the only modeled quantities in the dollar estimates. None is observed in public data.

| Input | Low | Base | High | Reasoning |
|---|---:|---:|---:|---|
| QMB patients with 2+ qualifying conditions | 65% | 80% | 90% | Duals carry more chronic conditions than other beneficiaries; APCM also needs "significant risk", a clinical judgment |
| Other patients with 2+ qualifying conditions | 50% | 65% | 80% | About two-thirds of traditional Medicare beneficiaries have 2+ chronic conditions |
| Capture (share of eligible patient-months billed) | 10% | 25% | 50% | Year-one CCM reached a small fraction of eligible patients; APCM has no time threshold |
| Consent | 50% | 75% | 90% | Patients must agree and accept cost sharing; QMBs owe none |

The base case gives $3.06B a year in allowed charges; the low and high cases give $0.70B and $8.27B. Full capture with full consent would be $14.0B to $18.4B depending on the condition shares.

## Forecast

| ID | Assumption | Value used | Note |
|---|---|---|---|
| A20 | Target | Practice has 1+ visible APCM row in the 2025 file | Pre-registered; frozen in `pipeline_output/forecast/frozen_2025_v1/FREEZE.md` |
| A21 | Training analog | G2211 uptake in 2024 from 2023 profiles (model A); new CCM/PCM in 2024 (model B, check) | No APCM outcome exists before the 2025 file |
| A22 | Model | Unpenalised logistic regression, standardised features | Interpretable; a shallow tree is a reasonable sensitivity check |
| A23 | Score | Percentile of model A probability | Probabilities are G2211-scaled, so only the ranking is used |
| A24 | Freeze | Frozen 2026-10-25T04:35:06Z, tag `forecast-2025-v1` | One-way; the freeze script refuses to overwrite |
