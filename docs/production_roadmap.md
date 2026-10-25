# Roadmap

What is done, what is next, and the gate for each phase.

## P0. Source integrity and national baseline (done)

- [x] Ingest CMS Physician & Other Practitioners files (by Provider, by Provider and Service, by Geography and Service) for 2019 to 2024 with URL, retrieval time and SHA-256 manifests.
- [x] Effective-dated code families for CCM, PCM, TCM, BHI, CoCM, RPM, AWV, ACP, G2211, SDOH navigation, APCM and office visits.
- [x] Primary care definition, practice roll-up, readiness tiers, suppression measurement.
- [x] dbt tests on every grain plus reconciliation tests.

## P1. Policy and payment engine (done)

- [x] APCM rules transcribed from the CY2025 and CY2026 final rules with Federal Register page cites (`seeds/billing_rules.csv`).
- [x] CY2026 RVUs, conversion factors and GPCIs; fee arithmetic matches CMS's National Payment Amount File in all 109 localities.
- [x] Allowed amount, patient coinsurance and QMB cost-sharing protection separated.
- [ ] Medicare payment net of sequestration, and supplemental coverage of coinsurance.

**Gate:** every amount and rule traces to an official document and version. Met.

## P2. National attribution and equity (mostly done)

- [x] Practice links from CMS Doctors and Clinicians, with solo clinicians kept separate.
- [x] Dual-eligible counts, county QMB ratios, rurality, HPSA and SVI joined with join-rate diagnostics.
- [x] Suppression measured by code and family against national totals.
- [x] Remove post-acute and nursing-facility clinicians: no visible office visits, or nursing facility and home visits outnumbering them.
- [ ] Quantify FQHC, RHC and Medicare Advantage coverage gaps by state.

**Gate:** every estimate has a denominator, suppression coverage and join rates. Met for national and state results.

## P3. Forecast (in progress)

- [x] Literature reviewed; contribution stated against the published survey of APCM uptake.
- [x] Target, features and evaluation plan pre-registered in the model card.
- [x] Interpretable logistic model with cross-validated AUROC and Brier score.
- [x] Freeze the forecast before CMS publishes the 2025 file (frozen 2026-10-25, tag `forecast-2025-v1`).
- [ ] Score it against the 2025 file when published: AUROC, average precision, calibration by decile, uptake by dual-share fifth.

**Gate:** an immutable, timestamped forecast, then a public scorecard of where it was wrong.

## P4. Product (in progress)

- [x] Report page on GitHub Pages, rebuilt on every pipeline run.
- [x] Streamlit app: findings, practice finder, rule-cited planner, locality payment calculator; headless tests in CI.
- [ ] Validate the planner and calculator with a primary care practice manager and a billing lead.
- [x] Practice one-page brief from the app (profile, billing, payment, first steps with rule citations), printable to PDF.

## P5. Patient-level logic (optional)

- [ ] Test monthly QMB status, condition look-backs and same-month billing conflicts on CMS's synthetic claims files. Logic test only; synthetic patients carry no findings.

## Not in scope without a real client

Multi-user accounts, saved plans, claims storage and live EHR or billing integrations. Those need a real user, a data-governance agreement and a privacy review first.
