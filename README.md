# APCM Opportunity — Prototype

A reproducible DuckDB + dbt project for estimating practice-level Advanced Primary Care Management (APCM) opportunity from beneficiary-level analytic inputs. The included data are fictional and exist only to exercise the pipeline.

## Start here

1. Read [`docs/module_1_spec.md`](docs/module_1_spec.md) and [`docs/assumptions_log.md`](docs/assumptions_log.md). They were authored before implementation.
2. Create a Python environment and install `requirements.txt`.
3. Run `python scripts/make_demo_data.py` to regenerate the deterministic fictional inputs.
4. Run `dbt build --project-dir . --profiles-dir .` from this directory.
5. Run `streamlit run app.py` for an interactive practice opportunity view.

The synthetic input is not a CMS Synthetic RIF extract. No national findings, forecasts, billable-claim conclusions, or practice identities are produced. Demo payment rates are editable illustrative placeholders, not a fee-schedule transcription. Replace them with year- and locality-specific CMS PFS data before any real analysis.

## Public CMS provider data

The source inventory is in [`docs/data_source_inventory.md`](docs/data_source_inventory.md). The public 2024 CMS Physician & Other Practitioners by Provider and Service file is available through the CMS Data API. Download predecessor care-management and preventive-service code rows with:

```bash
python scripts/download_public_provider_use.py --year 2024
```

The script writes a source manifest and a filtered CSV under `data/public_raw/`; raw data is git-ignored. Refresh the `--dataset-id` from CMS's Access API page when a new reporting-year release appears. The committed project does not include the raw extract. CMS provider service data can support NPI-level, suppression-aware readiness measures, but it is aggregated FFS Part B data and does not include beneficiary-level APCM claims, monthly QMB status, or actual patient-level overlap. Use CMS Synthetic RIF files to test beneficiary-level logic; do not generalize synthetic findings to real practices.

## Project layout

- `seeds/`: editable APCM rate/scenario and code-family reference inputs.
- `data/`: deterministic, fictitious beneficiary-month and practice profile inputs.
- `models/staging/`: typed source views.
- `models/intermediate/`: tier assignment and scenario expansion.
- `models/marts/`: practice opportunity and readiness output.
- `tests/`: dbt singular checks; `schema.yml` defines uniqueness and accepted values.
- `docs/`: specification, assumptions, literature scan and validity report.
- `scripts/`: demo data generation, CMS public-data download, and forecast freeze utility.

## Data contract for real data

`beneficiary_months.csv` must contain one row per beneficiary-month with stable de-identified beneficiary and practice keys, month, qualifying chronic condition count, monthly QMB flag, practice attribution source, and observed overlapping care-management allowed amount if known. Public aggregate NPI files cannot supply that grain; do not infer beneficiary-level conflicts from aggregate totals. `practice_profiles.csv` contains denominator and readiness signal features. Keep direct identifiers out of this project.

## Methods and caveats

Tier eligibility follows the documented prototype rules: G0558 for QMB beneficiaries with at least two qualifying conditions; otherwise G0557 for at least two conditions; otherwise G0556. This maps to the CMS APCM overview, while final-rule text must still be transcribed with Federal Register page citations before production. Gross opportunity applies capture and consent assumptions to illustrative rates. The displacement measure is only populated when beneficiary-month overlap data are supplied. Coinsurance is a modeled 20% exposure for non-QMB patients and zero for QMBs, not an adjudicated liability calculation.

Readiness proxies use prior CCM, TCM and behavioral health billing intensity. They do not verify the operational requirements CMS lists (care plan, urgent access, continuity, consent, etc.). See the assumptions log for low/base/high inputs.

## Citation starting points

- [CMS APCM services overview](https://www.cms.gov/medicare/payment/fee-schedules/physician-fee-schedule/advanced-primary-care-management-services)
- [CY2025 PFS final rule, Federal Register 89 FR 97710 onward](https://www.federalregister.gov/documents/2024/12/09/2024-25382/medicare-and-medicaid-programs-cy-2025-payment-policies-under-the-physician-fee-schedule-and-other)
- [CY2026 PFS final rule](https://www.cms.gov/medicare/payment/fee-schedules/physician/federal-regulation-notices/cms-1832-f)
- [Reddy et al. 2020, Annals of Family Medicine](https://doi.org/10.1370/afm.2573)
- [Informing APCM: care coordination trends 2020–2023](https://doi.org/10.7812/TPP/25.040)
- [Primary Care Clinician Uptake of Medicare APCM Billing Codes (online 2026-10-22)](https://doi.org/10.1007/s11606-026-10949-8)
- [CMS Medicare Physician & Other Practitioners API](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service/api-docs)
- [CMS data API documentation](https://data.cms.gov/api-docs)
- [CMS synthetic claims collection](https://data.cms.gov/collection/synthetic-medicare-enrollment-fee-for-service-claims-and-prescription-drug-event)

## Forecast integrity

The freeze utility writes an immutable CSV plus a SHA-256 manifest with a user-supplied freeze timestamp. It refuses to overwrite an existing freeze. Run only on a real, documented prediction file after its outcome definition, input cutoff and source snapshot are recorded. This demo intentionally ships without a real forecast.

A two-page CEO brief template is in `docs/client_brief_template.md`. The intended Tableau Public view is represented here by a Streamlit prototype; the mart table can be exported as a Tableau input once a valid national/practice dataset has been loaded.

