# Production roadmap and completion criteria

The portfolio prototype is useful today as a public-data provider signal explorer and architecture demonstration. “National APCM opportunity for every practice” requires completing the following evidence and data work; the repo avoids presenting an illustrative model as that finished product.

## P0 — Source integrity and public baseline (implemented)

- [x] Retrieve public 2024 CMS Physician & Other Practitioners provider-service data through the documented API.
- [x] Save source metadata and row counts; keep raw and derived extracts out of Git.
- [x] Map predecessor care-management codes by effective date and roll to NPI.
- [x] Show code-family breadth, geographies, filters, and caveats in a public-data dashboard.
- [x] Record hash lineage from source CSV and reference table to the derived view.

## P1 — Beneficiary-level logic validation (not complete)

- [ ] Download and inventory the CMS Synthetic RIF archive; record file names, data dictionary, reporting years, sizes, and join keys.
- [ ] Implement claim-header/line and enrollment adapters with stable pseudonymous beneficiary keys; never commit the source files.
- [ ] Implement CCW condition algorithms and exact lookback/claim-type rules from the year-specific CCW documentation.
- [ ] Compute monthly QMB status from enrollment; test end-of-month, partial eligibility, and missing-month cases.
- [ ] Attribute primary care using a sourced, versioned service/specialty code set and deterministic tie handling.
- [ ] Validate one tier per beneficiary-month and prove no claim amounts from synthetic files drive PFS price calculations.

**Completion gate:** an end-to-end synthetic run produces an eligibility ledger, source-reconciliation diagnostics, and expected edge-case fixtures without reporting synthetic results as real findings.

## P2 — Policy and financial engine (not complete)

- [ ] Transcribe APCM requirements, consent/frequency, exceptions and same-practitioner overlap policies from CY2025 and CY2026 final rules, claims manual, and official code guidance into cited effective-dated tables.
- [ ] Implement all billing-code families with start/end dates, base/add-on relationships, modifier and place-of-service notes.
- [ ] Ingest official annual RVUs, locality GPCIs, conversion factors, and payment files; reconcile against CMS published amounts for representative localities and dates.
- [ ] Separate allowed amount, Medicare payment, beneficiary cost-sharing, supplemental coverage, and QMB state liability semantics.

**Completion gate:** every amount and rule traces to a specific official document/file/version, and calculation differences against authoritative examples are explained.

## P3 — National attribution and equity baseline (not complete)

- [ ] Build and validate NPI-to-organization/practice links; preserve ambiguous/multi-site attribution instead of forcing a one-to-one mapping.
- [ ] Define provider panel denominators and unique beneficiary estimates from valid sources; do not derive patient intensity from service-unit sums.
- [ ] Add matched state/national totals to quantify suppression where definitions and denominators reconcile.
- [ ] Join rurality, HPSA, SVI and dual-enrollment context with published crosswalk vintage and join-rate diagnostics.
- [ ] Quantify FQHC/RHC, Medicare Advantage, provider-group, and small-cell coverage gaps before equity comparisons.

**Completion gate:** every estimate has a denominator, suppression coverage, join rates, population coverage, and an uncertainty range; small-cell and missing-setting handling is documented.

## P4 — Forecast, dashboard and external validation (not complete)

- [ ] Review the published APCM uptake study and prior care-management literature; state the incremental contribution accurately.
- [ ] Pre-register target, observation date, predictors, freeze timestamp, and scoring protocol before using the outcome dataset.
- [ ] Fit a simple interpretable model with time-appropriate predictors; publish calibration, discrimination, subgroup error, and limitations.
- [ ] Validate dashboard definitions and client brief with a primary-care operator; distinguish estimate, forecast, and observed claims.

**Completion gate:** public forecast artifact is immutable and scoreable; after outcome release, a reproducible scorecard reports where the model was wrong.

## Not in scope without a real client deployment

Cloud hosting, multi-tenant authentication, row-level permissions, claims storage services, alerting, and live operational integrations. Those require an actual user, data-governance agreement, threat model, and operating owner before architecture is selected.

