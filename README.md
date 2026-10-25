# APCM Readiness Atlas

**All findings in this repository come from real CMS, HRSA, CDC and Census public data.**

Medicare's Advanced Primary Care Management codes (G0556, G0557, G0558) started paying primary care practices a monthly per-patient fee in January 2025. The top tier, G0558, is for Qualified Medicare Beneficiaries (QMBs): low-income patients enrolled in both Medicare and Medicaid. This project sizes the APCM opportunity for U.S. primary care and asks whether the practices that see the most QMB patients are ready to bill it.

**[Open the app](https://anandiganguli97-apcm-opportunity-app-l8sdm0.streamlit.app/)** to explore findings, look up a practice, build an implementation plan or estimate APCM payment. **[Read the report](https://anandiganguli97.github.io/apcm-opportunity/)** for the one-page version.

## What you can do in the app

- **National findings:** the 2019 to 2024 trend, equity cuts by dual-eligible share, rurality, shortage area and social vulnerability, where QMB patients get care, CCM vs APCM payment, the national opportunity and the data's blind spots.
- **Practice finder:** search 51,000+ primary care practices by name or clinician NPI. Each profile shows what the practice already bills, its patient mix, estimated QMB patients and its draft readiness score.
- **Implementation planner:** a self-check that turns into a sequenced workplan with owners, tasks and "ready when" checks. Start it from a practice and it shows what that practice's billing already suggests for each area. Every area cites the Federal Register rule behind it, and the plan downloads as Markdown.
- **Payment calculator:** what APCM could pay a practice at CMS's real 2026 amounts for its Medicare locality, by level, with patient coinsurance and a comparison with CCM.

The app reads the pipeline's committed outputs, so it starts instantly and never downloads source data. It asks for no patient information.

## Findings

Service year 2024 unless noted; CY2026 payment rates. Each figure links to the file it comes from.

1. **Care management was rare before APCM.** 5.6% of 215,245 primary care clinicians had visible chronic or principal care management (CCM/PCM) billing in 2024, up from 4.6% in 2019. Remote monitoring grew fastest (0.1% to 1.9%). Half bill annual wellness visits. ([`national_trend.csv`](pipeline_output/results/national_trend.csv))
2. **QMB patients sit with less-ready practices.** Where most patients are dual-eligible, 25% of estimated QMB patients are with a practice showing no visible care management at all, against 9% in the practices with the fewest duals. ([`readiness_by_dual_quintile.csv`](pipeline_output/results/readiness_by_dual_quintile.csv))
3. **But readiness is U-shaped, not a straight gradient.** 9.2% of clinicians with the fewest dual-eligible patients bill CCM or PCM, 4.4% in the middle fifth, and 7.7% among clinicians whose panels are mostly dual-eligible. In primary care shortage counties, 11.0% of dual-eligible patients have a clinician who bills CCM or PCM, against 12.9% elsewhere. ([`equity.csv`](pipeline_output/results/equity.csv))
4. **APCM pays less per month than CCM but can pay more per year.** G0557 is $53.78 a month against $66.13 for the base CCM code, with no monthly time minimum. The median 2024 CCM biller billed 4.5 months per patient ($383 a year at 2026 rates); G0557 billed all 12 months is $645, more than CCM for 84% of CCM billers. G0558 every month is $1,407 per QMB patient. ([`ccm_vs_apcm_summary.csv`](pipeline_output/results/ccm_vs_apcm_summary.csv), [`fee_schedule_2026.csv`](pipeline_output/results/fee_schedule_2026.csv))
5. **National opportunity: $0.7B to $8.3B a year in allowed charges** for traditional Medicare (base case $3.1B), depending on capture, consent and the share of patients meeting the two-condition criterion. Full enrollment would be $14.0B to $18.4B. ([`apcm_opportunity_national.csv`](pipeline_output/results/apcm_opportunity_national.csv), assumptions in [`docs/assumptions_log.md`](docs/assumptions_log.md))
6. **Draft readiness score.** A logistic model trained on how practices took up G2211, a primary care code launched in 2024, ranks every practice for likely APCM uptake (cross-validated AUROC 0.80). The least-ready tenth of practices holds 3.6 times the QMB patients its share of all patients would suggest, and averages a 57% dual-eligible panel. A check model trained on new CCM/PCM adoption (AUROC 0.74) ranks practices similarly (Spearman 0.73), but the two disagree on dual share: high-dual practices were slower to add G2211 and more likely to start care management. ([`pipeline_output/forecast/`](pipeline_output/forecast/))
7. **The data has blind spots, and they are measured.** CMS hides clinician-code rows with fewer than 11 patients. That hides 3.9% of CCM services but 39% of transitional care management services, so TCM-based readiness is understated for small practices. ([`suppression_by_family.csv`](pipeline_output/results/suppression_by_family.csv), [`docs/data_validity_report.md`](docs/data_validity_report.md))

The closest prior work is a survey of 404 primary care clinicians in which 14.9% reported using APCM (Grumbach et al., *JGIM*, October 2026). This project is the national, claims-based complement. See [`docs/literature_scan.md`](docs/literature_scan.md).

**Checked against the sources.** Every fee used here matches CMS's published 2026 payment amounts in all 109 Medicare localities to the cent, the APCM rules are transcribed from the Federal Register with page citations ([`docs/policy_evidence.md`](docs/policy_evidence.md)), and the G2211 uptake that trains the forecast is consistent with a 100% claims study (Ganguli et al., *JAMA* 2026). Full checks in [`docs/data_validity_report.md`](docs/data_validity_report.md).

## The forecast is not frozen yet

The readiness score is a pre-registered forecast of which practices will show APCM billing in the 2025 CMS file, which is not yet published. It stays a draft until it is frozen with [`scripts/freeze_forecast.py`](scripts/freeze_forecast.py), which writes a timestamped SHA-256 manifest and never overwrites. The target, features, training design and evaluation plan are in [`model_card_draft.json`](pipeline_output/forecast/model_card_draft.json).

## How it works

```
CMS / HRSA / CDC / Census  ->  pipeline/ingest.py      download, hash, filter to Parquet (not committed)
                           ->  pipeline/profile.py     aggregate profile of every staged file
                           ->  dbt (DuckDB)            staging -> intermediate -> marts, with data tests
                           ->  pipeline/export.py      aggregate CSVs in pipeline_output/results
                           ->  pipeline/forecast.py    draft readiness score and model card
                           ->  pipeline/build_dashboard.py   report page, published to GitHub Pages
pipeline_output/  ->  app.py (Streamlit)   findings, practice finder, planner, calculator
```

The source sites are often unreachable from sandboxed environments, so the pipeline runs on GitHub Actions (`.github/workflows/pipeline.yml`): put a job name in `pipeline/JOB` and push. The workflow restores cached Parquet, runs `pipeline/run.sh`, and commits the outputs and report back to the branch. A second workflow runs the app's tests headless on every change.

Run the app locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Rebuild the data locally (needs network access to the source sites):

```bash
pip install -r requirements-pipeline.txt
python pipeline/ingest.py mup && python pipeline/ingest.py reference && python pipeline/ingest.py pfs
python pipeline/profile.py
dbt build --project-dir . --profiles-dir .
python pipeline/export.py && python pipeline/forecast.py && python pipeline/build_dashboard.py
```

## Repository layout

| Path | Contents |
|---|---|
| `pipeline/` | Ingestion, profiling, export, forecast and dashboard build scripts; `hcpcs_codes.json` code families |
| `models/staging`, `intermediate`, `marts` | dbt models. Key marts: `mart_national_trend`, `mart_equity`, `mart_practice`, `mart_ccm_vs_apcm`, `mart_apcm_opportunity_national`, `mart_suppression` |
| `seeds/` | Primary care definition, effective-dated code families, the only scenario assumptions (`apcm_scenarios.csv`), policy rule register |
| `tests/` | dbt data tests |
| `pipeline_output/` | Manifests with source URLs and SHA-256, profile, results, draft forecast, last run log |
| `app.py`, `src/apcm_opportunity/` | Streamlit app ([live](https://anandiganguli97-apcm-opportunity-app-l8sdm0.streamlit.app/)); `app_tests/` runs it headless |
| `dashboard/` | Report page: `template.html` and the built `index.html` ([live](https://anandiganguli97.github.io/apcm-opportunity/)) |
| `docs/` | [Methods](docs/methods.md), [assumptions](docs/assumptions_log.md), [data validity](docs/data_validity_report.md), [sources](docs/data_source_inventory.md), [literature](docs/literature_scan.md), [policy evidence](docs/policy_evidence.md), [chronic conditions](docs/chronic_conditions.md), [literature log](docs/literature.csv), [architecture](docs/architecture.md), [data dictionary](docs/data_dictionary.md), [decision log](docs/decision_log.md), [roadmap](docs/production_roadmap.md), client brief template |

## Limits

Traditional Medicare Part B professional claims only: no Medicare Advantage, and no FQHC or RHC care billed under their own payment systems. QMB counts are estimates (each clinician's dual-eligible count times the county QMB share). Practices come from the current CMS Doctors and Clinicians snapshot. Billing a code shows a workflow exists; it does not prove a practice meets APCM's requirements. Details in [`docs/methods.md`](docs/methods.md).

## Sources and references

- CMS: Medicare Physician & Other Practitioners (by Provider; by Provider and Service; by Geography and Service), 2019 to 2024; Doctors and Clinicians national file; Medicare Monthly Enrollment; Medicare Geographic Variation; PFS Relative Value Files RVU26D.
- HRSA primary care HPSA detail; CDC/ATSDR SVI 2022; Census 2020 ZCTA to county relationship file.
- [CMS APCM overview](https://www.cms.gov/medicare/payment/fee-schedules/physician-fee-schedule/advanced-primary-care-management-services); [CY2025 PFS final rule](https://www.federalregister.gov/documents/2024/12/09/2024-25382/medicare-and-medicaid-programs-cy-2025-payment-policies-under-the-physician-fee-schedule-and-other); [CY2026 PFS final rule](https://www.cms.gov/medicare/payment/fee-schedules/physician/federal-regulation-notices/cms-1832-f).
- Ganguli et al. [Billing of Medicare's G2211 Longitudinal Care Code Among Traditional Medicare Beneficiaries](https://jamanetwork.com/journals/jama/fullarticle/2845315), *JAMA*, 2026. Agarwal et al. Adoption of Medicare's Transitional Care Management and Chronic Care Management Codes in Primary Care, *JAMA*, 2018.
- Grumbach et al. [Primary Care Clinician Uptake of Medicare APCM Billing Codes](https://doi.org/10.1007/s11606-026-10949-8), *JGIM*, 2026. Reddy et al. [Use of Chronic Care Management Among Primary Care Clinicians](https://doi.org/10.1370/afm.2573), *Ann Fam Med*, 2020. [Informing APCM: care coordination trends 2020 to 2023](https://doi.org/10.7812/TPP/25.040), *Perm J*, 2025.

## About the build

AI coding assistants (OpenAI Codex and Anthropic Claude Code) were used to speed up implementation. The research question, data choices, assumptions and interpretation are documented with the results, and every number traces to a public file and a script.

CPT codes and descriptions are copyright American Medical Association.
