# APCM Readiness Atlas: contributor guide

## Overview

Sizes Medicare's Advanced Primary Care Management (APCM, HCPCS G0556 to G0558, effective January 2025) opportunity for U.S. primary care practices from public CMS data, and tests whether the practices serving the most Qualified Medicare Beneficiaries (QMBs), who qualify for the highest-paying level, are ready to bill it. Outputs are a reproducible data pipeline, a report page and a Streamlit app.

## Engineering rules

- **Real data only.** No fictional or simulated data in any finding. Every number in the README, report and app traces to a public source file and a script.
- **Aggregates only in Git.** Raw downloads and staged Parquet are never committed (`data/processed/` is git-ignored). Only aggregate outputs go in `pipeline_output/`.
- **The frozen forecast is immutable.** Never modify `pipeline_output/forecast/frozen_2025_v1/`. Any new freeze is a new version directory and needs the project owner's sign-off.
- **Changes go through pull requests.** Work on a feature branch and open a pull request to `main`; do not push to `main` directly.
- **Cite rules and check fees.** APCM rules come from `seeds/billing_rules.csv` (Federal Register page cites); fee arithmetic must keep matching the CMS National Payment Amount File.

## Pipeline

The source sites (CMS, HRSA, CDC, Census, Federal Register) are often unreachable from sandboxed development environments, so the pipeline runs on **GitHub Actions** (`.github/workflows/pipeline.yml`).

1. Put the job name in `pipeline/JOB` (`probe`, `probe2`, `ingest`, `analyze` or `references`). For `references`, list the steps in `pipeline/REFERENCE_STEPS`.
2. Push the branch. The workflow triggers on changes under `pipeline/`, `models/`, `seeds/`, `tests/`, `dbt_project.yml` and `requirements-pipeline.txt`.
3. The workflow restores the staged-data cache, runs `pipeline/run.sh`, saves the cache (even on failure), commits `pipeline_output/` and `dashboard/index.html` back to the branch, and republishes the report to the `gh-pages` branch. Log in `pipeline_output/last_run.log`, status in `pipeline_output/last_run_status.txt`.
4. Pull the branch to read results. Add `[skip ci]` to a commit message to push without a run.

With network access to the sources, the same steps run locally: `pip install -r requirements-pipeline.txt`, then `python pipeline/ingest.py mup|reference|pfs`, `python pipeline/profile.py`, `dbt build --project-dir . --profiles-dir .`, `python pipeline/export.py`, `python pipeline/forecast.py`, `python pipeline/build_dashboard.py`.

## Layout

- `pipeline/ingest.py`: resolves every source from its publisher (data.cms.gov `data.json` for CMS files), downloads, hashes (SHA-256), filters, writes Parquet plus manifests in `pipeline_output/manifests/`.
- `pipeline/references.py`: Federal Register rule text, CMS payment amount check, CCW condition definitions (`pipeline_output/references/`).
- `pipeline/hcpcs_codes.json` and `seeds/code_families.csv`: effective-dated HCPCS families (CCM, PCM, TCM, BHI, CoCM, RPM, AWV, ACP, G2211, SDOH navigation, APCM, office E/M).
- `pipeline/profile.py`: aggregate profile of staged data (`pipeline_output/profile/profile.json`).
- `models/staging`, `models/intermediate`, `models/marts`: dbt-duckdb models. Key marts: `mart_national_trend`, `mart_suppression`, `mart_clinician`, `mart_practice`, `mart_equity`, `mart_ccm_vs_apcm`, `mart_apcm_opportunity_national`.
- `seeds/primary_care_specialties.csv`: primary care definition (physicians in FM, IM, GP, geriatrics; NPs and PAs only with visible wellness-visit billing). `int_clinician_year` keeps only office-based clinicians: visible office visits, not outnumbered by nursing facility plus home and residence visits (`int_clinician_year_candidates` keeps the rest with flags).
- `seeds/apcm_scenarios.csv`: the only modeled inputs (share of patients meeting the 2+ chronic condition criterion, capture, consent), labeled as scenario assumptions.
- `pipeline/export.py`: `pipeline_output/results/*.csv`, `headline.json`, the practice extract and the NPI to practice lookup.
- `pipeline/forecast.py`: readiness score and 2025 forecast, regenerated each run; the forecast of record is frozen in `pipeline_output/forecast/frozen_2025_v1/` (never modify it). `pipeline/build_dashboard.py`: report page from `dashboard/template.html`.
- `app.py` + `src/apcm_opportunity/dashboard.py`: Streamlit app (findings, practice finder, planner, payment calculator) reading committed `pipeline_output/`. Tests in `app_tests/` run headless on Python 3.11 and 3.14 (`.github/workflows/app-check.yml`; Streamlit Community Cloud runs 3.14). App deps in `requirements.txt`, pipeline deps in `requirements-pipeline.txt`.
- `docs/`: methods, assumptions, data sources, validity report, policy evidence, chronic conditions, literature, architecture, data dictionary, decision log, roadmap, client brief template.

## Data sources (all public)

CMS Medicare Physician & Other Practitioners (by Provider, by Provider and Service, by Geography and Service), service years 2019 to 2024; CMS Doctors and Clinicians national file (clinician to group practice, current snapshot); CMS Medicare Monthly Enrollment (county QMB and dual counts); CMS Geographic Variation PUF (traditional Medicare counts); CMS 2026 Physician Fee Schedule RVU release D with GPCIs; CMS National Payment Amount File 2026; HRSA primary care HPSA; CDC/ATSDR SVI 2022 county; Census 2020 ZCTA to county relationship; CY2025 and CY2026 PFS final rules.

## Status

Done:
- Pipeline green end to end (all dbt models and tests passing). Results in `pipeline_output/results/`.
- Validation in `docs/data_validity_report.md`: reconciliations, suppression by code family, fee arithmetic matching CMS in all 109 localities, APCM rules transcribed with Federal Register cites.
- Report live at https://anandiganguli97.github.io/apcm-opportunity/; app live at https://anandiganguli97-apcm-opportunity-app-l8sdm0.streamlit.app/.
- 2025 forecast frozen 2026-10-25T04:35:06Z (`pipeline_output/forecast/frozen_2025_v1/`, tag `forecast-2025-v1`).

Next:
1. When CMS publishes the 2025 service-year file, score the frozen forecast per `FREEZE.md` and publish the results next to it.
2. Optional: synthetic claims logic-test module; locality-adjusted payment in the national model.
