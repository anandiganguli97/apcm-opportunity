# Module 1 — Claims-to-opportunity specification

**Version:** 0.1.0  
**Authored:** 2026-10-24  
**Purpose:** Define the analysis in plain language before implementation.  
**Status:** Prototype specification; not a billing compliance determination.

## Question
For each attributed primary-care practice, how many traditional Medicare beneficiary-months appear clinically eligible for each APCM tier, what would modeled APCM payments be under explicit capture assumptions, and what observed care-management revenue might be displaced in the same month? Do practices with the largest estimated G0558 populations show lower observed readiness?

## Unit of analysis
The core analytic grain is one beneficiary × calendar month × attributed practice. Practice summaries aggregate these rows. A beneficiary is attributed to the practice with the most qualifying primary-care service units in a defined lookback window; ties are resolved deterministically by most recent qualifying service, then lowest stable practice identifier. This is an analytic proxy inspired by MSSP claims-based plurality assignment, not official MSSP assignment.

## Eligibility and tier assignment
- APCM eligibility begins no earlier than 2025-01-01. Rules and code sets are effective-dated.
- The prototype interprets G0556 as the base tier for a beneficiary with zero or one qualifying chronic condition; G0557 requires at least two; G0558 requires at least two and QMB status in the service month.
- G0558 takes precedence over G0557 for QMB beneficiaries who otherwise meet the chronic-condition threshold.
- Chronic-condition flags are derived from a versioned ICD-10-CM value set and condition-specific CCW lookback algorithm. The starter model accepts condition flags directly because the synthetic input layout is not present in this workspace; ICD claim diagnosis expansion is a subsequent adapter.
- QMB status must be month-specific. “Dual eligible” is not assumed to equal QMB without a mapping in the enrollment source.
- Consent, service-element documentation, primary-care responsibility and practitioner eligibility are not observable in public aggregate files. Estimates therefore represent clinical / claims-based addressable opportunity, not billable claims.

## Attribution, conflicts and payment
- Primary-care attribution uses a documented, configurable list of service codes and clinician specialties. Official MSSP rules must be separately transcribed and cited before production use.
- Same-month care-management services that CMS says are included in APCM are treated as potentially displaced only when attributable to the same billing practitioner, consistent with the final rule. Public provider-level aggregates cannot establish same beneficiary-month overlap; the demo marks this as an uncertainty, rather than subtracting all practice-level historical revenue as if it were certain.
- Gross APCM payment = eligible beneficiary-months × tier-specific national non-facility PFS allowed amount × capture rate × consent rate. This prototype does not apply geographic adjustment unless locality-level PFS RVU/GPCI inputs are supplied.
- Net modeled change = gross projected APCM payment minus modeled same-month displaced care-management allowed amount. Beneficiary coinsurance exposure is estimated at 20% of allowed amount for non-QMB beneficiaries; QMB cost sharing is modeled as zero. Actual liability depends on coverage and adjudication.
- Rates are year-specific and must come from the official PFS file / fee schedule. Synthetic claim payment amounts are not used as fee schedule estimates.

## Readiness and scenarios
Readiness is a proxy, not a verified inventory of infrastructure. It combines observed CCM, TCM, BHI and collaborative-care use intensity per 100 attributed beneficiaries. Code use is evidence that some workflows may exist; it does not prove 24/7 access, comprehensive care plans, patient consent, timely transitions, or operational capacity.

Practice-level tier mix is not observed in suppressed national provider aggregates. Where beneficiary-level synthetic data are available, tiers are counted directly. Where only aggregate data exist, scenario tier mix combines practice dual share and chronic prevalence using an explicit independence assumption; low/base/high ranges vary prevalence, QMB share and capture/consent. Do not present these estimates as measured patient-level tier counts.

## Outputs
1. Beneficiary-month opportunity ledger with eligibility tier, practice, QMB flag, estimated payment, and conflict flags when source detail permits.
2. Practice-level opportunity statement: addressable months by tier, gross payment, possible displaced revenue, net modeled change and coinsurance exposure, each labeled by scenario and data coverage.
3. Readiness and equity views stratified by rurality, shortage designation, social vulnerability and dual share, only when those join keys and complete denominators are available.
4. Data validity and suppression reconciliation report.
5. A frozen, timestamped forecast of 2025 APCM adoption, with model specification and scorecard protocol. This is a forecast artifact, not an assertion of observed 2025 adoption.

## Claims we will not make from this prototype
- National actual APCM adoption, because the relevant 2025 utilization file is not yet present and provider/service aggregates do not identify patient-month detail.
- Exact displaced revenue or patient-level conflicts from practice-level aggregate files.
- Equity conclusions for FQHC/RHC settings, Medicare Advantage, or suppressed cells without external data.
- Clinical eligibility, documented consent, or billing compliance solely from diagnosis codes and enrollment status.

## Literature scan checkpoint (2026-10-24)
The premise that no APCM uptake paper exists is already stale: a Journal of General Internal Medicine paper on primary-care clinician uptake was published online 2026-10-22. It must be reviewed before the forecast is framed as novel. Prior studies include Reddy et al. on CCM use (Annals of Family Medicine, 2020; DOI 10.1370/afm.2573) and the 2025 Permanente Journal care-coordination trend study (DOI 10.7812/TPP/25.040). The short scan is not yet a systematic review; see `literature_scan.md` for search terms and screening steps.
