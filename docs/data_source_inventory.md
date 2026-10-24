# Data source inventory

All sources are public. `pipeline/ingest.py` resolves each one from its publisher at run time (data.cms.gov's `data.json` catalog for CMS files), downloads it, records the URL, retrieval time and SHA-256 in `pipeline_output/manifests/`, and keeps only the columns and codes the models use. Raw files and staged Parquet are never committed.

| Source | Publisher | Years | Used for | Grain and limits |
|---|---|---|---|---|
| Medicare Physician & Other Practitioners, by Provider | CMS | 2019 to 2024 | Clinician type, location, RUCA, patient counts, dual counts, HCC risk, chronic condition prevalence | NPI and year. Traditional Medicare Part B. Dual fields blank for small panels. Names and street addresses dropped at ingestion |
| Medicare Physician & Other Practitioners, by Provider and Service | CMS | 2019 to 2024 | Visible billing of care management, preventive, G2211, APCM and office visit codes | NPI, HCPCS and setting. Rows under 11 beneficiaries removed. Filtered to the codes in `pipeline/hcpcs_codes.json` (2.17M of 9.78M rows in 2024) |
| Medicare Physician & Other Practitioners, by Geography and Service | CMS | 2019 to 2024 | National and state totals to measure suppression | Geography, HCPCS and setting |
| Doctors and Clinicians national file | CMS | Current snapshot | Clinician to group practice (Org PAC ID) | 3.63M rows, 1.64M NPIs, 83,666 organizations |
| Medicare Monthly Enrollment | CMS | Annual rows 2019 to 2025 | County and state counts of duals and QMBs | Includes Medicare Advantage enrollees |
| Medicare Geographic Variation, by National, State and County | CMS | 2014 to 2024 | Traditional Medicare beneficiary count (opportunity denominator) | Traditional Medicare only |
| PFS Relative Value Files, release RVU26D | CMS | CY2026 | RVUs, conversion factor and GPCIs for APCM and comparison codes | National amounts used; GPCIs staged for later locality work |
| Primary care HPSA detail | HRSA | Current | Counties with a designated geographic primary care shortage area | Designations change continuously |
| Social Vulnerability Index, county | CDC/ATSDR | 2022 | County SVI percentile | Ecological; one vintage |
| ZCTA to county relationship file | Census | 2020 | Clinician ZIP to county | ZIPs without a ZCTA do not match |

## Not used, and why

- **CMS Synthetic Medicare claims (synthetic RIF).** Useful for testing patient-level eligibility and conflict logic, but synthetic patients carry no findings. The download sits behind a JavaScript page; it remains an optional logic-test module.
- **2025 Physician & Other Practitioners files.** Not yet published. They are the outcome for the frozen forecast.
- **Medicare Advantage encounter data.** Not public.

## Running the pipeline

The CMS, HRSA, CDC and Census sites are often unreachable from sandboxed environments, so the pipeline runs on GitHub Actions (`.github/workflows/pipeline.yml`). Set the job in `pipeline/JOB` and push; the workflow restores the staged-data cache, runs `pipeline/run.sh`, and commits `pipeline_output/` and `dashboard/index.html` back to the branch. Locally, with network access to those hosts:

```bash
pip install -r requirements.txt
python pipeline/ingest.py mup
python pipeline/ingest.py reference
python pipeline/ingest.py pfs
python pipeline/profile.py
dbt build --project-dir . --profiles-dir .
python pipeline/export.py
python pipeline/forecast.py
python pipeline/build_dashboard.py
```
