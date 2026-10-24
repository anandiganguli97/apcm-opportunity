# Data dictionary

## Public CMS provider baseline

The downloadable source is an annual CMS provider-service aggregate. `scripts/build_public_readiness.py` applies `seeds/code_families.csv` effective dates and outputs one row per rendering NPI for providers with at least one mapped historical readiness code row.

| Output field | Meaning | Important caveat |
|---|---|---|
| `provider_npi` | 10-digit rendering provider NPI | Provider identity, not a validated practice group. |
| `state`, `zip5`, `ruca_code`, `provider_type` | Coarse provider descriptors from CMS | Conflicts across source rows are blanked; address is not a service area. |
| `reporting_year` | CMS claims reporting year | This baseline predates APCM. |
| `observed_code_count` | Distinct mapped HCPCS codes with rows | Suppression can hide rows. |
| `observed_care_management_families` | Count of CCM, complex CCM, PCM, TCM, BHI, CoCM families with visible nonzero service units | Breadth proxy only; no operational capacity is observed. |
| `readiness_breadth_index` | `100 × observed family count ÷ 6` | Not a probability, normalized rate, or billability score. |
| `service_volume_units` | Sum of CMS `Tot_Srvcs` across selected care-management rows | Counts service units, not unique people or beneficiary-months; code units may differ. |
| `{family}_service_units` | Code-family service-unit sum for each mapped family | Suppressed/absent rows are not treated as true zero use. |
| `has_{family}_signal` | Whether at least one nonzero service row was observed for a family | False means not observed in this file; it does not prove non-use. |
| `metadata_conflict_fields` | Provider descriptors that differed across source rows | Empty means no conflict detected in this extract, not an independent identity validation. |

The lineage JSON stores raw-source and code-catalog SHA-256 hashes, output hash, source manifest path, row counts, and metric definition.

## Fictional beneficiary-month sandbox

| Input field | Meaning | Caveat |
|---|---|---|
| `beneficiary_id` | Stable fictional demo ID | Not a CMS ID and not a real person. |
| `service_month` | Month the modeled tier applies to | Should be a calendar-month date. |
| `practice_id` | Fictional attributed-practice key | Attribution is a demo assumption. |
| `qualifying_chronic_count` | Precomputed condition count | Does not currently derive from claim diagnosis lines/CCW algorithms. |
| `qmb_flag` | Fictional monthly QMB indicator | Not an official enrollment determination. |
| `consent_proxy` | Fictional consent stand-in | Does not establish documented consent. |
| `observed_care_mgmt_allowed_amount` | Fictional same-month possible overlap amount | Not adjudicated or rule-validated displacement. |
| `attribution_method` | Demo method label | Not official MSSP attribution. |

## Units and money

The dbt opportunity mart is denominated in beneficiary-months and modeled allowed dollars. The default rate seed is explicitly `illustrative_placeholder`; do not use it as a CMS payment output. Coinsurance is a modeled exposure, not beneficiary liability.

