# Policy evidence

APCM rules used in this project, transcribed from the Federal Register text of the CY2025 PFS final rule (document 2024-25382, 89 FR 97710) and the CY2026 PFS final rule (document 2025-19787). The pipeline's `references` job downloads both rules from govinfo.gov and keeps every APCM passage tagged with its page (`pipeline_output/references/fr_*_apcm.txt`, hashes in `manifest.json`). The rule-by-rule register with citations is [`seeds/billing_rules.csv`](../seeds/billing_rules.csv).

## Rules that shape the analysis

| Rule | What the final rule says | Citation | How the project uses it |
|---|---|---|---|
| Levels | G0556: one or fewer qualifying chronic conditions. G0557: two or more. G0558: a QMB with two or more. A qualifying condition is expected to last 12 months or until death and puts the patient at significant risk | 89 FR 97871, 97872, 97875 | Level mix in the opportunity model; the two-or-more share is a scenario input because no public file measures the clinical criterion |
| Billing | Once per calendar month, no minimum time, by the practitioner responsible for all primary care; not every element is needed every month | 89 FR 97867-97868 | Patient-months times monthly rate; CCM vs APCM comparison assumes the CCM biller switches to APCM |
| Duplicative services | The APCM practitioner may not bill CCM, PCM, TCM, interprofessional consultation, remote image/video evaluation, virtual check-ins or e-visits for the same patient in the same month. Other practitioners, including in the same practice, may | 89 FR 97894, 97896 | Readiness tiers treat CCM/PCM as the closest workflow to APCM; CCM revenue is replaced, not added, when comparing per-patient amounts |
| Allowed alongside APCM | BHI, community health integration, principal illness navigation, SDOH risk assessment, RPM and RTM | 89 FR 97897 | Multi-service readiness tier counts BHI and RPM as complements |
| Cost sharing | Providers may not bill QMBs for Medicare cost sharing | 89 FR 97875 | Coinsurance modeled at 20% for non-QMB patients and zero for QMBs |
| Consent and initiating visit | Documented consent at initiation (verbal is fine); initiating visit only for new patients; an AWV by the APCM practitioner counts | 89 FR 97880-97882 | Consent rate is a scenario input; wellness-visit billing is part of the readiness signal |
| Practice requirements | 24/7 access for urgent needs, care plan, care transitions follow-up within 7 days when possible, care coordination, enhanced communication, population management | 89 FR 97883-97890 | Not observable in claims; stated as a limit of billing-based readiness |
| Performance measurement | MIPS eligible clinicians report the Value in Primary Care MVP; ACO and APM participants meet it through those programs | 89 FR 97893-97894 | Context for why ACO-affiliated practices may adopt first |
| Valuation | Work RVUs 0.25, 0.77 and 1.67 | 89 FR 97900-97901 | Matches the staged CY2026 RVU file exactly |
| 2026 add-ons | G0568, G0569 (collaborative care) and G0570 (BHI) billed with an APCM base code by the same practitioner in the same month; FQHCs and RHCs may report them | 90 FR 49470, 49552 | Staged and priced; not part of the base opportunity |

Final-rule text takes precedence over CMS summaries and vendor guides. Table 26 (the duplicative-services list) is an image in the Federal Register, so its service list is taken from the text that introduces it on 89 FR 97894.

## Forecast protocol

Implemented in `pipeline/forecast.py`; see the forecast section of [`methods.md`](methods.md). The target, features, training design and evaluation plan are recorded in `pipeline_output/forecast/model_card_draft.json` with source hashes and the repository commit. Freezing (`scripts/freeze_forecast.py`) happens once, before the 2025 file is published, and never overwrites a prior freeze.
