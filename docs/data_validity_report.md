# Data validity report — prototype status

The project began with fictional demo data. On 2026-10-24, the CMS public 2024 Physician & Other Practitioners by Provider and Service API was accessed and filtered records were retrieved for care-management codes. This confirmed the endpoint, schema, and existence of 2024 predecessor-code data. A probe returned 1,263 rows for 99484 and 3,017 for 99487; the 99490 response filled the 5,000-row page, so it must be paginated before interpreting its total. These are provider-service rows, not national beneficiary counts. No full extract was staged; no suppression percentages, reconciliation totals, missing-population estimates, or national equity results have been calculated. The demo's fictional rows are not used to infer national characteristics.

The source and limitation inventory is maintained in [`data_source_inventory.md`](data_source_inventory.md). The documented downloader writes raw extracts outside Git under `data/public_raw/`.

## Required checks when data arrive

- Reconcile practice/NPI sums with state and national totals; quantify suppressed rows by code and geography where totals permit. Never treat a suppressed cell as zero.
- Compare institutional and professional claims coverage; separately identify FQHC/RHC payment pathways and quantify excluded populations. Confirm file-specific claim coverage rather than assuming a file has no institutional data.
- State that Medicare Advantage is outside traditional FFS claims data unless a separate source is joined.
- Audit incident-to and group billing; rendering clinician may differ from billing NPI.
- Verify monthly dual/QMB enrollment and incomplete months.
- Confirm beneficiaries with multiple practices and attribution tie rates.
- Reconcile fee schedule-derived allowed amounts against official published PFS locality rates, not synthetic paid amounts.
- Report missing diagnosis, identifier, locality, and social-risk join rates.

## Suppression calculation template

For each geography × code, define visible beneficiary count as the sum of published non-suppressed counts and authoritative total as the state/national published total. `invisible_share = 1 - visible / authoritative_total`. This is only valid when totals use matching populations, years, code definitions, and suppression rules. If not reconcilable, label unmeasured.

