# Data validity report

**Data as of:** pipeline run on 2026-10-24 (service years 2019 to 2024). Source files, retrieval times and SHA-256 hashes are in `pipeline_output/manifests/`. Aggregate profiles of every staged file are in `pipeline_output/profile/profile.json`.

## Automated checks (dbt, 48 of 48 passing)

- Unique keys on every staging and mart grain (`models/schema.yml`).
- `assert_dual_not_above_total`: no clinician has more dual-eligible patients than total patients.
- `assert_visible_not_above_national`: visible clinician-level services never exceed the national total for a code and year.
- `assert_apcm_rates_loaded`: G0556, G0557 and G0558 each have a positive 2026 non-facility rate.

## Reconciliations

| Check | Result |
|---|---|
| Traditional Medicare beneficiaries, 2024 (Geographic Variation, national row) | 27,732,177; total Medicare 71,035,683, Medicare Advantage 33,677,969 |
| Dual and QMB enrollment, 2024 (Monthly Enrollment) | County rows sum to 12,160,400 duals against a national row of 12,167,130 (99.9%). QMBs (only plus plus) are 68.5% of duals nationally |
| CMS 2026 conversion factor in the RVU file | $33.4009 (non-qualifying APM) and $33.5675 (qualifying APM) |
| APCM amounts | RVU times conversion factor: G0556 0.49 RVU, $16.37; G0557 1.61, $53.78; G0558 3.51, $117.24 |
| Clinician file rows | One row per NPI per year in all six years (1,155,870 in 2019 to 1,296,739 in 2024) |
| HPSA designation labels | "Geographic HPSA" and "High Needs Geographic HPSA" present as `stg_hpsa_county` expects; only rows with status "Designated" are used |
| Provider type labels | "Family Practice", "Internal Medicine", "General Practice", "Geriatric Medicine", "Nurse Practitioner", "Physician Assistant" match the seed exactly |

## Suppression: what the clinician-level file cannot see

CMS removes clinician-code-setting rows with fewer than 11 beneficiaries. The share of national services missing from clinician-level rows (by-Geography-and-Service national totals minus visible rows):

| Family | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|---:|
| Chronic care management | 3.6% | 3.9% | 4.3% | 4.4% | 4.0% | 3.9% |
| Principal care management | | 9.8% | 5.8% | 6.2% | 7.6% | 7.1% |
| Transitional care management | 30.9% | 38.1% | 37.7% | 38.8% | 38.4% | 38.7% |
| Behavioral health integration | 9.8% | 6.1% | 5.4% | 4.6% | 5.0% | 3.9% |
| Collaborative care | 21.9% | 54.4% | 55.9% | 51.3% | 44.4% | 35.7% |
| Remote monitoring | 7.3% | 6.4% | 6.7% | 6.3% | 6.5% | 6.0% |
| Wellness visits | 7.2% | 7.5% | 7.0% | 6.9% | 6.8% | 6.8% |
| Advance care planning | 6.9% | 7.2% | 7.1% | 6.9% | 6.8% | 6.5% |
| Visit complexity add-on (G2211) | | | | | | 1.4% |
| Social needs and navigation | | | | | | 8.4% |

What follows from this:

- **CCM and PCM readiness are well measured.** Fewer than 1 in 25 CCM services are hidden. The 2024 code 99490 has 6.92M national services and 6.68M visible.
- **TCM readiness is understated.** 99495 is 43% invisible: 100,735 clinician rows nationally, 18,207 visible. TCM is typically a handful of patients per clinician per year, so many TCM billers never appear. Tier 1 and tier 3 counts lean on TCM and are lower bounds.
- **Collaborative care is mostly invisible** at the clinician level (36% to 56% of services), so the BHI/CoCM readiness signal is weak.
- The initial Welcome to Medicare visit (G0402) is 60% invisible, which matters only for the NP/PA inclusion rule; the annual codes G0438 and G0439 carry it.

## Coverage of the joined measures (2024)

| Measure | Coverage |
|---|---|
| Dual-eligible count | Blank for 464,482 of 1,296,739 providers (all specialties). 150,899 of 215,245 primary care clinicians (70%) have a reported count; equity and QMB results use only these |
| Practice assignment | 357,285 of 3,630,233 Doctors and Clinicians rows list no organization; those NPIs count as solo practices. 2024 primary care rolls up to 51,451 practices |
| Rurality (RUCA) | 77 of 150,899 clinicians unknown |
| County (ZIP to county) and SVI | 4,617 of 150,899 clinicians (3.1%) have no county SVI value, mostly ZIPs with no ZCTA (PO boxes, unique ZIPs) |
| QMB ratio | County ratio when the county has 100+ duals, otherwise the state ratio |

## Known limitations

- **Traditional Medicare, Part B professional claims only.** Medicare Advantage patients are absent, and so are FQHC and RHC visits billed under their own payment systems. Practices serving many MA or FQHC patients look less ready than they are.
- **Rendering clinician, not billing practice.** Incident-to services billed under a supervising physician show up under that physician.
- **Practice membership is a 2026 snapshot** applied to every year from 2019.
- **QMB counts are ecological estimates** (county ratio applied to a clinician's duals). They will be off where a practice's duals differ from the county mix.
- **Patient counts summed across clinicians double count** patients who see several clinicians in the same practice (`patient_panel_proxy`).
- **Join keys are validated at ingestion.** SVI county FIPS must be numeric (pandas returns selected columns in file order, so columns are renamed by name, never by position), and the GPCI file is parsed by header text because CMS changes its columns between releases.
