# Methods

**Last updated:** 2026-10-24. Every number in the README and dashboard comes from files under `pipeline_output/`, which the GitHub Actions pipeline writes from the public sources in [`data_source_inventory.md`](data_source_inventory.md).

## Question

Advanced Primary Care Management (APCM, HCPCS G0556, G0557, G0558) started on January 1, 2025. It pays a monthly per-patient fee with three levels. The top level, G0558, is for Qualified Medicare Beneficiaries (QMBs) with two or more chronic conditions. This project asks:

1. How much care management did primary care practices bill before APCM (2019 to 2024)?
2. Do clinicians and practices serving dual-eligible and QMB patients show the same readiness as others?
3. What would APCM pay per patient compared with chronic care management (CCM), and what is the national opportunity under stated assumptions?
4. Which practices are most likely to bill APCM first? (A forecast to be frozen before 2025 data are published.)

## Units

- **Clinician-year.** One row per NPI and service year in the CMS by-Provider file, restricted to individuals (entity code I).
- **Practice.** One organization (Org PAC ID) per NPI from the current CMS Doctors and Clinicians file. About 260,000 clinicians are listed with more than one organization, often including national therapy and post-acute companies with thousands of members, so the practice is the organization with the highest share of primary care clinicians among its members, then the one the NPI is listed with most often, then the larger organization, then lowest ID. NPIs with no organization are their own practice (`npi:<NPI>`). CMS publishes no historical snapshot, so the current file assigns practices for every year.

## Primary care definition

`seeds/primary_care_specialties.csv`:

- Physicians with CMS provider type Family Practice, Internal Medicine, General Practice or Geriatric Medicine.
- Nurse practitioners and physician assistants only in years they have a visible annual or initial wellness visit row (G0438, G0439, G0402). Without this, the NP and PA counts (203,212 and 112,514 in 2024) would swamp the physician count with specialty-practice clinicians.
- Keeping only office-based clinicians: a clinician needs visible office visits (99202 to 99215) in the year, and their nursing facility (99304 to 99310) plus home and residence visits (99324 to 99350) must not outnumber them. The rest are mostly post-acute, long-term care and house-call clinicians, whose patients are not the office panels APCM is built for. They stay in `int_clinician_year_candidates` with flags for each reason, and `mart_primary_care_exclusions` (exported as `results/primary_care_exclusions.csv`) reports how many are removed each year.

## Code families

`pipeline/hcpcs_codes.json` and `seeds/code_families.csv` (effective-dated):

| Family | Codes |
|---|---|
| Chronic care management (CCM) | 99490, 99439, 99491, 99437, 99487, 99489, G2058, G0506 |
| Principal care management (PCM) | 99424 to 99427, G2064, G2065 |
| Transitional care management (TCM) | 99495, 99496 |
| Behavioral health integration (BHI) | 99484, G0323 |
| Collaborative care (CoCM) | 99492, 99493, 99494, G2214 |
| Remote monitoring (RPM) | 99453, 99454, 99457, 99458, 99091 |
| Wellness visits (AWV) | G0438, G0439, G0402 |
| Advance care planning (ACP) | 99497, 99498 |
| Visit complexity add-on | G2211 |
| Social needs and navigation | G0019, G0022, G0023, G0024, G0136 |
| APCM | G0556, G0557, G0558 and the 2026 behavioral health add-ons G0568 to G0570 |
| Office visits | 99202 to 99205, 99211 to 99215 |

## Visibility and suppression

A clinician "bills" a family when the by-Provider-and-Service file has at least one row for that clinician and a code in the family. CMS omits rows for fewer than 11 beneficiaries, so absence means "fewer than 11 patients or none", never zero. `mart_suppression` compares visible clinician-level services with the national totals in the by-Geography-and-Service file to measure what is hidden (see [`data_validity_report.md`](data_validity_report.md)).

`benes_min` for a family is the largest beneficiary count on any one code in the family: a floor on unique patients, because patients can appear under several codes. CCM patient-months are the services of first-unit monthly codes (99490, 99491, 99487 and the PCM equivalents).

## Policy rules and condition definitions

APCM rules are transcribed from the final rules with page cites in [`policy_evidence.md`](policy_evidence.md) and `seeds/billing_rules.csv`. The chronic condition columns in the by-Provider file and their CCW look-back periods are in [`chronic_conditions.md`](chronic_conditions.md).

## Dual-eligible and QMB estimates

- Dual-eligible count per clinician is `Bene_Dual_Cnt` from the by-Provider file. CMS blanks both dual fields for small panels (464,482 of 1,296,739 providers in 2024), so equity tables cover the 150,899 of 215,245 primary care clinicians with a reported count.
- QMB patients are not in any clinician-level public file. The estimate is the clinician's dual count times the county ratio `(QMB only + QMB plus) / all duals` from CMS Medicare Monthly Enrollment (annual rows, same year), using the clinician's ZIP mapped to the county with most of its land area (Census 2020 ZCTA relationship file). Counties with fewer than 100 duals use the state ratio.
- Nationally in 2024, QMBs were 8.33M of 12.17M dual enrollees (68%).

## Readiness tiers (practice level)

`mart_practice.readiness_tier`, from visible 2024 billing by any clinician in the practice:

| Tier | Rule |
|---|---|
| 3 Multi-service care management | CCM or PCM, plus BHI, CoCM, RPM or TCM |
| 2 CCM or PCM | CCM or PCM only |
| 1 Visit-based services only | TCM, ACP or AWV but no CCM or PCM |
| 0 No visible care management | none of the above |

Billing a code shows some workflow exists. It does not prove 24/7 access, care plans, consent processes or the other APCM requirements.

## Payment

National non-facility amounts are RVUs times the conversion factor from the CY2026 PFS relative value file, release D (October 2026). The non-qualifying-APM conversion factor ($33.4009) is used throughout; no geographic adjustment. 2026 rates: G0556 $16.37, G0557 $53.78, G0558 $117.24; 99490 $66.13.

`mart_ccm_vs_apcm` reprices each 2024 CCM biller's observed CCM services at 2026 rates and divides by their CCM patients, then compares with G0557 billed in the same number of months or in all 12.

## National opportunity

`mart_apcm_opportunity_national`:

- Patients: traditional Medicare beneficiaries in 2024 (Geographic Variation file, 27,732,177).
- QMB share: estimated QMB patients over total patients across primary care clinicians with dual counts (14.7%).
- Level mix: shares of QMB and other patients with two or more qualifying conditions are scenario inputs (`seeds/apcm_scenarios.csv`). No public file measures the APCM clinical criterion.
- Allowed amount = patient-months by level times 2026 rates times capture times consent. Coinsurance is 20% for non-QMB patients and zero for QMBs.

## Readiness score and 2025 forecast

`pipeline/forecast.py`, outputs in `pipeline_output/forecast/`.

- **Target (pre-registered):** a practice has at least one visible APCM row (G0556 to G0558) in the 2025 by-Provider-and-Service file.
- **Problem:** no APCM outcome exists yet to train on.
- **Design:** train on the closest real launch. Model A predicts visible G2211 billing in 2024 (the code launched January 2024) from each practice's 2023 profile. Model B, a check, predicts first visible CCM or PCM in 2024 among practices with neither in 2023.
- **Model:** unpenalised logistic regression on standardised features: log panel size, log clinician count, physician share, dual share, average HCC risk score, metropolitan share, CCM, PCM, TCM, BHI or CoCM, RPM, ACP, wellness-visit share of clinicians, with median imputation and missing flags. Flags with fewer than 50 practices in the minority class are dropped.
- **Validation:** 5-fold cross-validated AUROC and Brier score (`frozen_2025_v1/model_card.json`; `model_card_draft.json` is the same card regenerated on each run).
- **Score:** 2024 profiles scored with model A. `readiness_score` is the practice's percentile (0 to 100) of the predicted probability. The probabilities describe G2211 uptake, so only the ranking carries over to APCM.
- **Definitions at freeze:** the frozen file keeps the practice and primary care definitions of its commit (tag `forecast-2025-v1`), and the outcome will be built with that tagged code. Later refinements to those definitions change the descriptive results, not the forecast or how it is scored.
- **Freeze:** frozen on 2026-10-25T04:35:06Z with `scripts/freeze_forecast.py` (SHA-256 manifests, never overwrites) in `pipeline_output/forecast/frozen_2025_v1/`, with the target, method, scoring protocol and source hashes in `FREEZE.md`. When CMS publishes the 2025 file, evaluation will report AUROC, average precision, uptake by decile and uptake by decile within dual-share fifths, against the naive rule "billed CCM or PCM in 2024".

## What this does not claim

- Observed 2025 APCM uptake. That file is not published yet.
- Patient-level eligibility, consent or same-month billing conflicts, which need beneficiary claims.
- Anything about Medicare Advantage, or FQHC and RHC care billed under their own payment systems.
- Causal effects of readiness on outcomes.
