# Results

Service year 2024 unless noted. Payment at CY2026 national non-facility rates. Every figure comes from a file in `pipeline_output/`; the README lists the headline findings with links.

## Readiness before APCM

| Measure | 2019 | 2024 |
|---|---:|---:|
| Office-based primary care clinicians | 190,519 | 202,294 |
| Billing chronic or principal care management | 4.1% | 4.9% |
| Billing transitional care management | 13.3% | 11.5% |
| Billing remote monitoring | 0.1% | 1.9% |
| Billing annual wellness visits | 45.3% | 51.0% |
| Billing G2211 (launched 2024) | | 31.0% |

Source: `results/national_trend.csv`. The 12,951 candidates who are not office-based are left out; they bill CCM or PCM at 17.5%, so including them would put the 2024 share at 5.6% (`results/primary_care_exclusions.csv`).

## Practices by readiness tier

| Tier | Practices | Clinicians | Estimated QMB patients |
|---|---:|---:|---:|
| No visible care management | 20,183 | 28,162 | 654,563 |
| Visit-based services only | 22,397 | 103,679 | 2,164,220 |
| CCM or PCM only | 1,783 | 5,998 | 148,367 |
| Multi-service care management | 2,836 | 64,455 | 1,388,550 |

Source: `results/readiness_tiers.csv`. Large multi-site organizations dominate the multi-service tier because any site's billing counts for the whole organization.

## Equity

- **By dual-eligible share of the panel**, CCM or PCM billing falls and then ticks up: 9.1% of clinicians in the lowest fifth, 3.9% in the middle, 3.1% in the fourth and 4.5% in the highest.
- **Where QMB patients are:** in the fifth of practices with the most dual-eligible patients, 29% of estimated QMB patients are with a practice showing no visible care management, against 9% in the fifth with the fewest.
- **Shortage areas:** 8.9% of dual-eligible patients in geographic primary care HPSA counties have a clinician billing CCM or PCM, against 7.4% elsewhere.

Sources: `results/equity.csv`, `results/readiness_by_dual_quintile.csv`.

## Payment

G0556 $16.37, G0557 $53.78 and G0558 $117.24 a month; base CCM (99490) $66.13. The median 2024 CCM biller billed 4.8 months per patient, $398 a year at 2026 rates. G0557 every month is $645; it pays more than observed CCM billing for 84% of CCM billers. Sources: `results/fee_schedule_2026.csv`, `results/ccm_vs_apcm_summary.csv`.

## National opportunity (traditional Medicare)

| Scenario | Allowed per year | Patient coinsurance |
|---|---:|---:|
| Low | $0.68B | $0.10B |
| Base | $2.99B | $0.44B |
| High | $8.11B | $1.21B |

Inputs in `seeds/apcm_scenarios.csv` and `docs/assumptions_log.md`. Source: `results/apcm_opportunity_national.csv`.

## Readiness score (frozen forecast)

Logistic model trained on G2211 uptake in 2024 from 2023 practice profiles: 47,564 practices, cross-validated AUROC 0.80. The least-ready tenth of practices holds 3.6 times the QMB patients its share of all patients would suggest. A check model on new CCM/PCM adoption has AUROC 0.74 and ranks practices similarly (Spearman 0.73). Frozen on 2026-10-25 (`forecast/frozen_2025_v1/FREEZE.md`). The frozen file scores 51,451 practices under the definitions at its commit; 46,359 of today's 47,199 practices (with 99% of estimated QMB patients) carry a frozen score. Source: `forecast/frozen_2025_v1/model_card.json`, `forecast/qmb_by_readiness_decile.csv` (computed from the frozen file).

## What the data cannot show

Patient-level APCM eligibility, consent, or same-month billing conflicts; Medicare Advantage; FQHC and RHC care billed under their own payment systems; and anything under CMS's 11-beneficiary suppression threshold. See `docs/data_validity_report.md`.
