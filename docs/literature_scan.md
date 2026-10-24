# Literature review

**Search date:** 2026-10-24. **Method:** structured web search of journal, government and grey literature, with every result screened and logged in [`literature.csv`](literature.csv). This is a structured scoping review, not a full systematic review: one reviewer, no database-specific Boolean searches (PubMed, Embase), and full text was read where open access.

## Searches

| ID | Search string | Purpose |
|---|---|---|
| S1 | `"advanced primary care management" Medicare uptake claims study 2026` | Direct APCM uptake evidence |
| S2 | `G0556 G0557 G0558 APCM adoption primary care practices analysis` | Code-level adoption analyses |
| S3 | `chronic care management billing uptake Medicare primary care dual-eligible disparities study` | Predecessor-code adoption and equity |
| S4 | `G2211 complexity add-on code uptake 2024 Medicare primary care study` | The forecast's training event |
| S5 | `transitional care management principal care management uptake Medicare claims trends 2019 2023 journal` | Pre-APCM trends in the study window |

Inclusion: U.S. Medicare analyses of APCM or its predecessor care management codes (CCM, PCM, TCM) or of G2211 uptake, from claims, surveys or government reports. Exclusion: vendor and billing-guide content, studies outside primary care adoption (telehealth mode, hospital discharge programs), and studies that predate 2016 data.

## Results

13 records screened: 9 included, 4 excluded (including about 15 vendor pages logged as one grey-literature record). Detail in [`literature.csv`](literature.csv).

**APCM uptake.** One study measures it. Grumbach, Duffy and Etz (*JGIM*, October 2026) surveyed primary care clinicians about a year after launch: about 15% reported using APCM, and many had not heard of the codes. No claims-based APCM study exists yet, because CMS has not published 2025 service-year claims. A vendor source notes the public file has no G0556 to G0558 rows through 2024, which matches this project's data.

**Predecessor codes.** Uptake has always been low and concentrated. By 2016, 6.9% of practices with primary care physicians billed any CCM and 21.5% any TCM (Agarwal et al., *JAMA* 2018). Larger practices and practices already using other new codes adopted first (Agarwal et al., *Health Affairs*). From 2020 to 2023, under 5% of eligible patients received CCM (*Permanente Journal* 2025). This project's 2024 figure, 5.6% of primary care clinicians with visible CCM or PCM billing, fits that history.

**Dual-eligible patients.** ASPE's analysis of 2019 claims found dual-eligible beneficiaries received CCM at somewhat higher rates but TCM at lower rates. That mixed pattern matches this project's U-shaped result: clinicians with the highest dual share bill CCM more often than those in the middle, while QMB patients are still overrepresented in practices with no visible care management.

**G2211 as a launch analog.** In 2024, 24.0% of clinicians with any G2211-eligible visit billed G2211, with primary care physicians billing at the highest rate per eligible visit (Ganguli et al., *JAMA* 2026). This project's 29.7% for primary care clinicians is consistent with a primary care subset. EHR data show G2211 rose from 5% of Medicare E/M visits in January 2024 to 19% by December (*Annals of Internal Medicine* 2026), so first-year uptake of a new primary care code is gradual. That supports using a launch-year analog for the APCM forecast.

## Positioning

The survey literature reaches clinicians' awareness, intentions and barriers. This project is the national, claims-based complement: every traditional Medicare primary care clinician in the CMS public files, readiness measured from billing rather than self-report, the QMB (G0558) population located relative to that readiness, and a practice-level forecast the 2025 claims file will test. Two findings from prior work shaped the design: practice size and prior use of new codes predict adoption (both are forecast features), and patient cost sharing deters care management enrollment, which matters less for QMBs, who owe none.
