# Project context for Claude Code

## What this is

Portfolio project for Anandi (public health research scientist moving into hospital and healthcare analytics consulting roles). It sizes Medicare's Advanced Primary Care Management (APCM, codes G0556-G0558, launched January 2025) opportunity for U.S. primary care practices, using **real CMS public data only**, and asks whether practices serving low-income dual-eligible (QMB) patients, who qualify for the highest-paying tier, are ready to bill it.

Target audience: recruiters for healthcare analytics and consulting roles (for example, a McKinsey healthcare analytics role asking for SQL, claims and code sets, Tableau or Power BI, and data skepticism).

## Hard rules

- **No fictional or simulated data anywhere in findings.** The original prototype ran on hand-made demo data; it was deleted on this branch. Every number in the README must trace to a real file and a script.
- Raw downloads and staged Parquet are never committed (`data/processed/` is git-ignored). Only aggregate outputs go in `pipeline_output/`.
- Do not freeze the 2025 adoption forecast (`scripts/freeze_forecast.py`) without asking Anandi first. It is a one-way step.
- Work on branch `real-data-rebuild` and open a pull request to `main` for her review. Do not push to `main`.
- Writing style for anything she will read or publish: no em dashes, natural human prose, no AI-sounding phrases, casual and direct in conversation, concise in external-facing text.
- Commit messages end with the Claude attribution trailer.

## How the pipeline runs

The CMS, HRSA, CDC and Census sites are often blocked from Claude sandboxes, so the pipeline runs on **GitHub Actions** (`.github/workflows/pipeline.yml`), which has open internet access.

1. Put the job name in `pipeline/JOB` (`probe`, `probe2`, `ingest`, or `analyze`).
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
- `docs/`: spec, assumptions log, data source inventory, validity report, literature scan. These still describe the old prototype in places and need rewriting against real results.

## Data sources (all public, real)

CMS Medicare Physician & Other Practitioners (by Provider, by Provider and Service, by Geography and Service), service years 2019-2024; CMS Doctors and Clinicians national file (clinician to group practice, current snapshot); CMS Medicare Monthly Enrollment (county QMB and dual counts); CMS Geographic Variation PUF (traditional Medicare counts); CMS 2026 Physician Fee Schedule RVU release D (October 2026) with GPCIs; HRSA primary care HPSA; CDC/ATSDR SVI 2022 county; Census 2020 ZCTA-county relationship.

## Status (as of 2026-10-24)

Done:
- Fictional demo data, demo app and demo models removed.
- Probes confirmed URLs and schemas (`pipeline_output/probe/`). Column names are identical across 2019-2024.
- Ingestion, dbt models, tests and export written. The dbt project passed a local dry run on tiny stand-in files (not committed).
- Ingestion of 2019-2023 provider files succeeded and is cached. A 2024 download hit a transient CMS error; retries and per-year skipping were added and a rerun was started (run 40111939288).

Next:
1. Check the latest run (`pipeline_output/last_run_status.txt`, `last_run.log`). Fix any dbt or export errors.
2. Sanity-check results against sources: national service totals vs the geography file, rates vs the PFS look-up tool, HPSA designation-type labels in `profile.json` (the `stg_hpsa_county` filter assumes 'Geographic HPSA' and 'High Needs Geographic HPSA'), provider type labels for the primary care seed.
3. Rewrite README around real findings: pre-APCM readiness trend, suppression (share of care management invisible at clinician level), equity (dual and QMB patients vs others; rurality; HPSA; SVI), CCM vs APCM revenue per patient, national opportunity range. One blunt line near the top: all findings use real CMS public data.
4. Rewrite `docs/` to match (assumptions log, data validity report with real suppression numbers, methods). Cite Grumbach et al., JGIM, Oct 22 2026 (survey: 14.9% self-reported APCM use, n=404) as the closest prior work and position this as the national claims-based complement.
5. Optional: patient-level ICD-10 module on CMS's synthetic RIF claims (download link is behind a JavaScript page; ask Anandi to download the ZIP or find the API link), clearly labeled as a logic test with no findings.
6. Readiness score and 2025 forecast: compute, but ask before freezing.
7. Open the pull request to `main`.

Anandi plans to build the Tableau Public dashboard herself from `pipeline_output/results/practice_extract_tableau.csv.gz`, and to write the client brief herself.
