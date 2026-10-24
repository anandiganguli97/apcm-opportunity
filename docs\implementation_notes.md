# Implementation notes and runbook

## Data contract

The prototype's `beneficiary_months.csv` is intentionally a compact, already-attributed analytic input. It does not parse institutional/professional claim diagnosis rows, run CCW algorithms, derive QMB from enrollment spans, or calculate plurality attribution. Production adapters must implement those transformations before the dbt staging interface and preserve provenance at the row level.

`practice_profiles.csv` demonstrates the output profile contract. A production join should preserve NPI/TIN/group identifiers only as permitted, a practice-level denominator, county/locality, rural classification, HPSA/MUA status, SVI source year, and observed care-management utilization measures. Public-use suppressed values must remain null/statused, never imputed as zero without a sensitivity analysis.

## Readiness score

For demonstration only:

`score = min(100, 2 × (CCM + TCM + BHI + CoCM monthly services per 100 attributed beneficiaries))`

This simple monotonic score is designed to expose the proxy and make it easy to challenge. It is not a validated predictor. It does not yet include denominator confidence, care-plan or 24/7 infrastructure survey responses, staffing, EHR capability, FQHC/RHC status, or missingness penalties.

## Payment and displacement

The sample rate table contains rounded values from the user's brief and is explicitly labeled `illustrative_placeholder`. In production, calculate locality-specific PFS allowed amounts from the CY-specific RVUs, work/PE/MP GPCIs, conversion factor and place of service; reconcile against CMS's published locality file. Do not use paid amounts from synthetic claims. The starter model has a row-level placeholder for observed same-month care-management amounts, but the associated displaced amount is still uncertain unless billing practitioner identity and finalized code-family concurrency rules are present.

## Reproducible forecast protocol

Before outcome data are used: lock the adoption target; list feature source years and publication cutoffs; split data only with temporal logic; fit a logistic model with frozen preprocessing; publish predictions and source hashes; record timestamp, repository commit, model coefficients, calibration plan and expected outcome release. Evaluate AUROC and precision-recall discrimination, Brier score/calibration slope/intercept, and subgroup performance by dual share, rurality and shortage area. Report all missingness and threshold choices. Never overwrite a prior freeze.
