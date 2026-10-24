# APCM Opportunity Lab

**A public-health portfolio project exploring where primary-care providers already have experience with care-management services—and what that may mean as Medicare introduces Advanced Primary Care Management (APCM).**

## The question

Primary-care teams do not all start APCM from the same place. Some already bill for chronic care management, behavioral health, or follow-up after a hospital stay. This project uses public Medicare data to make that prior experience visible and explore what questions should come next.

## Results at a glance

For the 2024 reporting year, the CMS public provider file contains visible prior-care-management billing signals for **45,603 provider NPIs**. **8,041** have visible signals in at least two of six service families. The analysis includes **14.1 million reported service units** across those codes.

These are provider billing records, not unique patients, APCM enrollments, or estimates of how much a practice could earn. CMS suppresses some low-volume provider-code records, so no visible record does not always mean no service was provided. See [results and interpretation](docs/results.md).

## Explore the dashboard

The Streamlit dashboard lets you explore provider signals by state, provider type, and rural-urban classification code, and download the filtered table. A separate teaching sandbox uses fictional data to show how assumptions can change a modeled APCM scenario. **The sandbox is illustrative; it is not an estimate of real practices.**

**Open the live dashboard:** [APCM Opportunity Lab](https://anandiganguli97-apcm-opportunity-app-l8sdm0.streamlit.app/)

## Data and limitations

The public view uses CMS's 2024 Medicare Physician & Other Practitioners by Provider and Service file. It covers Original Medicare fee-for-service Part B professional claims, grouped by rendering NPI, billing code, and place of service. It does not represent Medicare Advantage, a full patient panel, or a confirmed practice organization.

Because the source is provider-level and suppresses small beneficiary counts, it cannot determine who qualifies for APCM, compare patient-level health needs, or calculate practice revenue. The next useful public-health step is to pair the billing baseline with validated practice attribution and a suitable beneficiary-level source.

- [Results and interpretation](docs/results.md)
- [Data sources](docs/data_source_inventory.md)
- [How to run the dashboard](#run-it-yourself)

## Run it yourself

Requires Python 3.11 or later.

```bash
python -m pip install -r requirements.txt
python scripts/download_public_provider_use.py --year 2024
python scripts/build_public_readiness.py --year 2024
streamlit run app.py
```

The CMS download and refresh instructions are included so the results can be reproduced. On first launch, the hosted dashboard retrieves the public CMS extract and builds the results; later interactions use the downloaded copy in the app container. Raw source extracts are not committed.

## About the build

Codex was used to speed up code generation and implementation. The project’s data choices, assumptions, and interpretation limits are documented alongside the results.

## Sources

- [CMS public provider-service data](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service)
- [CMS APCM services and requirements](https://www.cms.gov/medicare/payment/fee-schedules/physician-fee-schedule/advanced-primary-care-management-services)
- [CMS data API documentation](https://data.cms.gov/api-docs)
- [CMS provider-service methodology](https://data.cms.gov/sites/default/files/2025-04/MUP_PHY_RY25_202350312_Methodology_508.pdf)





