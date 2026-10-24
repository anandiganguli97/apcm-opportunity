# Assumptions log

**Snapshot date:** 2026-10-24. Values below are prototype defaults, not CMS policy unless explicitly cited. Revise through version control with source, date, owner, and sensitivity impact.

| ID | Assumption | Base/default | Sensitivity / alternative | Why it matters | Evidence / status |
|---|---|---:|---|---|---|
| A01 | G0556 threshold | 0–1 qualifying chronic conditions | Confirm exact clinical wording from CY2025 final rule; no code-only clinical inference | Sets base tier denominator | CMS APCM page; final-rule transcription pending |
| A02 | G0557 threshold | ≥2 qualifying chronic conditions | CCW condition algorithms and lookback variants | Higher payment tier eligibility | CMS APCM page; CCW implementation pending |
| A03 | G0558 threshold | ≥2 conditions and QMB | Require monthly QMB indicator; do not substitute any dual category | Highest payment and equity result | CMS APCM page; monthly enrollment mapping pending |
| A04 | Tier precedence | QMB + ≥2 conditions maps to G0558, otherwise ≥2 to G0557 | Test against finalized policy text | Prevents double-counting tiers | Policy interpretation; verify exact language in 89 FR 97710+ |
| A05 | Code families | Effective-dated mappings for CCM, PCM, TCM, BHI, CoCM, AWV, ACP, RPM, APCM | Include predecessor / successor code dates and modifier/place-of-service rules | Trend comparability and displaced revenue | No complete code table yet; must be built from annual CMS files/rules |
| A06 | Primary-care attribution | Plurality of qualifying primary-care services in configurable lookback | Alternative 12-month / calendar-year windows; deterministic tie-break | Assigns patients and denominator to practice | Modeled after MSSP; not official MSSP attribution until exact rules are cited |
| A07 | Condition ascertainment | Patient has a condition when CCW value-set / lookback algorithm is met | Vary lookback and claim types; use all available claim types | Tier mix changes with claims completeness | CCW algorithms requested; source files not yet obtained |
| A08 | Practice readiness | Past CCM/TCM/BHI/CoCM billing signals some enabling workflows | Weightings low/base/high; zero use does not mean no infrastructure | Readiness score is not a compliance audit | Hypothesis; validate with literature and practice survey if possible |
| A09 | Tier mix from aggregates | Base case combines chronic prevalence and QMB share; independence unless joint data exist | Low/high correlation bounds / direct beneficiary data | Can distort G0558 estimate materially | Explicit ecological inference; disclose prominently |
| A10 | Capture rate | Scenario input; no point estimate hard-coded as fact | 10% / 30% / 60% illustrative, configurable | Dominates revenue forecast | Illustrative only; adoption study/model should inform before publication |
| A11 | Consent rate | Scenario input | 50% / 75% / 90% illustrative | Limits payable population | Consent is not visible in claims data |
| A12 | Payment basis | Official year-specific PFS amount; non-facility APCM rate by default | Locality-adjusted RVU × GPCI × CF; facility comparison if supported | Amounts differ by geography and setting | Official PFS inputs not yet staged; never use synthetic claim paid amounts |
| A13 | Coinsurance | 20% of allowed amount for non-QMB estimate | Note secondary coverage and claim-specific liability | Patient exposure estimate | Statutory/general default; verify APCM-specific rule text |
| A14 | QMB liability | Zero modeled beneficiary cost sharing | Distinguish QMB status / state Medicaid payment handling | Equity and exposure | CMS QMB policy source needs citation in production |
| A15 | Same-month conflicts | Included service families may not be separately billed by same practitioner for same patient/month | Respect practitioner, service and exceptions in finalized rule | Net opportunity / displacement | CY2025 final rule section II.G, Federal Register pages to transcribe |
| A16 | Suppression | ≤10 beneficiary cells suppressed in public provider/service data | Estimate invisibility by reconciliation; suppressed count is not inferable exactly without totals | Understates small practices / low volume codes | CMS dataset methodology; calculate when source file available |
| A17 | Missing populations | Traditional Medicare claims aggregates omit MA; FQHC/RHC institutional / alternate file coverage differs | Join supplemental CMS files and identify denominator | May bias safety-net equity comparisons | File-specific coverage audit required; do not assume absent categorically |
| A18 | 2025 outcome availability | Not available in current workspace | Refresh when CMS publishes and freeze extraction date | Forecast validation | Date and cadence are assumptions; re-check CMS release calendar |
| A19 | Forecast target | Practice billed ≥1 APCM code in 2025 | Alternative sustained uptake / minimum volume threshold | Controls model label | Pre-register exact label before outcome data release |
| A20 | Forecast model | Interpretable logistic model with pre-2025 features | Shallow tree as sensitivity | Reproducibility and explainability | No fitting until eligible training table and freeze date are documented |

## Scenario inputs (editable)

| Scenario | Capture | Consent | Chronic prevalence multiplier | QMB share multiplier |
|---|---:|---:|---:|---:|
| Low | 0.10 | 0.50 | 0.85 | 0.85 |
| Base | 0.30 | 0.75 | 1.00 | 1.00 |
| High | 0.60 | 0.90 | 1.15 | 1.15 |

The values are deliberately illustrative placeholders. Replace them with observed evidence before producing a client forecast.

## Required revisions before public release

1. Transcribe each APCM inclusion, consent, frequency and duplicate-billing rule from the CY2025 final rule and each 2026 add-on rule from the CY2026 final rule, with Federal Register page and exact effective date.
2. Load official year-specific RVU/GPCI/conversion factor inputs and verify published national amounts.
3. Obtain exact CCW condition files and document each algorithm's lookback.
4. Run a systematic literature search, including the October 22, 2026 APCM uptake study surfaced in the initial scan.
5. Obtain the actual synthetic RIF files and schema before claiming a complete patient-level engine.
