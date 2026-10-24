# Project context for Claude Code

## What this is

Portfolio project for Anandi (public health research scientist moving into hospital and healthcare analytics consulting roles). It sizes Medicare's Advanced Primary Care Management (APCM, codes G0556-G0558, launched January 2025) opportunity for U.S. primary care practices, using **real CMS public data only**, and asks whether practices serving low-income dual-eligible (QMB) patients, who qualify for the highest-paying tier, are ready to bill it.

Target audience: recruiters for healthcare analytics and consulting roles (for example, a McKinsey healthcare analytics role asking for SQL, claims and code sets, Tableau or Power BI, and data skepticism).

## Hard rules

- **No fictional or simulated data anywhere in findings.** Every number in the README and dashboard must trace to a real file and a script.
- Raw downloads and staged Parquet are never committed (`data/processed/` is git-ignored). Only aggregate outputs go in `pipeline_output/`.
- Do not freeze the 2025 adoption forecast (`scripts/freeze_forecast.py`) without asking Anandi first. It is a one-way step.
- Work on branch `real-data-rebuild` and open a pull request to `main` for her review. Do not push to `main`.
- Writing style for anything she will read or publish: no em dashes, natural human prose, no AI-sounding phrases, casual and direct in conversation, concise in external-facing text.
- Commit messages end with the Claude attribution trailer.
- Keep the repository reading as one complete project: no references in docs, comments, commit messages or PR text to earlier versions, prototypes or removed data.

## How the pipeline runs

The CMS, HRSA, CDC and Census sites are often blocked from Claude sandboxes, so the pipeline runs on **GitHub Actions** (`.github/workflows/pipeline.yml`), which has open internet access.

1. Put the job name in `pipeline/JOB` (`probe`, `probe2`, `ingest`, `analyze` or `references`).
2. Push to `real-data-rebuild`. The workflow triggers on changes under `pipeline/`, `models/`, `seeds/`, `tests/`, `dbt_project.yml`.
3. The workflow restores the staged-data cache, runs `pipeline/run.sh`, saves the cache (even on failure), and commits `pipeline_output/` back to the branch (log in `pipeline_output/last_run.log`, status in `pipeline_output/last_run_status.txt`).
4. Pull the branch to read results. Add `[skip ci]` to a commit message to push without triggering a run.

If the sandbox can reach data.cms.gov (Anandi can allow domains in claude.ai Settings > Capabilities), the same steps run locally: `python pipeline/ingest.py mup|reference|pfs`, `python pipeline/profile.py`, `dbt build --project-dir . --profiles-dir .`, `python pipeline/export.py`.

## Layout

- `pipeline/ingest.py`: resolves every source from its publisher (data.cms.gov `data.json` for CMS files), downloads, hashes (SHA-256), filters, writes Parquet plus manifests in `pipeline_output/manifests/`.
- `pipeline/hcpcs_codes.json` and `seeds/code_families.csv`: effective-dated HCPCS families (CCM, PCM, TCM, BHI, CoCM, RPM, AWV, ACP, G2211, SDOH/navigation, APCM, office E/M).
- `pipeline/profile.py`: aggregate profile of staged data (`pipeline_output/profile/profile.json`).
- `models/staging`, `models/intermediate`, `models/marts`: dbt-duckdb models. Key marts: `mart_national_trend`, `mart_suppression`, `mart_clinician`, `mart_practice`, `mart_equity`, `mart_ccm_vs_apcm`, `mart_apcm_opportunity_national`.
- `seeds/primary_care_specialties.csv`: primary care definition (physicians in FM, IM, GP, geriatrics; NPs and PAs only with visible AWV billing).
- `seeds/apcm_scenarios.csv`: the only modeled inputs (share of patients meeting the 2+ chronic condition criterion, capture, consent). Clearly labeled as scenario assumptions.
- `pipeline/export.py`: writes `pipeline_output/results/*.csv`, `headline.json`, and a gzipped practice-level extract for Tableau.
- `pipeline/forecast.py`: draft readiness score and 2025 forecast (not frozen). `pipeline/build_dashboard.py`: builds `dashboard/index.html`.
- `docs/`: methods, assumptions log, data source inventory, validity report, literature scan, policy evidence, all written against real results. `client_brief_template.md` is Anandi's.

## Data sources (all public, real)

CMS Medicare Physician & Other Practitioners (by Provider, by Provider and Service, by Geography and Service), service years 2019-2024; CMS Doctors and Clinicians national file (clinician to group practice, current snapshot); CMS Medicare Monthly Enrollment (county QMB and dual counts); CMS Geographic Variation PUF (traditional Medicare counts); CMS 2026 Physician Fee Schedule RVU release D (October 2026) with GPCIs; HRSA primary care HPSA; CDC/ATSDR SVI 2022 county; Census 2020 ZCTA-county relationship.

## Status (as of 2026-10-24, end of day)

Done:
- Pipeline green end to end on real data (all dbt models and tests passing). Results in `pipeline_output/results/`, draft forecast in `pipeline_output/forecast/`.
- Sanity checks recorded in `docs/data_validity_report.md`.
- Dashboard: `dashboard/index.html`, built by `pipeline/build_dashboard.py` from `dashboard/template.html`, rebuilt and committed by CI after every analyze run, then force-published to the `gh-pages` branch (live at https://anandiganguli97.github.io/apcm-opportunity/). A gzipped practice-level extract is also exported for Tableau.
- README and `docs/` describe the real findings and methods.
- Reference checks (`pipeline/references.py`, job `references`, steps chosen in `pipeline/REFERENCE_STEPS`): APCM rules transcribed from the Federal Register into `seeds/billing_rules.csv`; fee arithmetic matches the CMS National Payment Amount File in all 109 localities; CCW condition definitions in `docs/chronic_conditions.md`; literature log in `docs/literature.csv`.
- Readiness score and draft 2025 forecast computed (`pipeline/forecast.py`, G2211-launch analog). NOT frozen.

Next:
1. Anandi to review the pull request to `main`.
2. Decide whether and when to freeze the forecast (`scripts/freeze_forecast.py`); must happen before CMS publishes the 2025 service-year file. Ask Anandi first.
3. Optional: synthetic RIF logic-test module (needs the ZIP; download link is behind a JavaScript page).
4. Optional: locality-adjusted payment using the staged GPCIs.
