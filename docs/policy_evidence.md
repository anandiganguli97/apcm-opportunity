# Literature and policy evidence note

The initial scan is evidence that the novelty statement needs revision, not a substitute for a formal literature review. Searches on 2026-10-24 located an online-first 2026 APCM uptake paper published 2026-10-22, in addition to the predecessor-code papers cited in the Module 1 specification. Before stating a research gap, obtain and screen full texts, references, and citation trails. Compare datasets, practice definitions, uptake periods, outcome thresholds and equity dimensions.

Policy sources reviewed in the initial implementation:

- CMS APCM overview: tier criteria, once-per-month limit, consent, initiating visit, and service elements. This is operational guidance; final-rule text takes precedence.
- CY2025 PFS final rule: APCM policy discussion at 89 FR 97859–97902; concurrent/duplicative services discussion at 89 FR 97894–97897; effectiveness January 1, 2025.
- CY2026 PFS final rule: APCM behavioral-health add-ons at 90 FR 49464–49471; codes G0568–G0570 are add-ons when the APCM base is reported by the same practitioner in the same month.

See `seeds/billing_rules.csv` for rule-level structured citations and verification status. It is a rules register starter; users must confirm specific passages against the official final rule before using it for compliance or a live claim engine.

## Forecast protocol

Implemented in `pipeline/forecast.py`; see the forecast section of [`methods.md`](methods.md). The target, features, training design and evaluation plan are recorded in `pipeline_output/forecast/model_card_draft.json` with source hashes and the repository commit. Freezing (`scripts/freeze_forecast.py`) happens once, before the 2025 file is published, and never overwrites a prior freeze.
