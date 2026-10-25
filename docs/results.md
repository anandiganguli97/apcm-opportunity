# Results

Service year 2024 unless noted. Payment at CY2026 national non-facility rates. Every figure comes from a file in `pipeline_output/`; the README lists the headline findings with links.

## Readiness before APCM

| Measure | 2019 | 2024 |
|---|---:|---:|
| Primary care clinicians | 203,376 | 215,245 |
| Billing chronic or principal care management | 4.6% | 5.6% |
| Billing transitional care management | 13.2% | 11.6% |
| Billing remote monitoring | 0.1% | 1.9% |
| Billing annual wellness visits | 44.5% | 50.4% |
| Billing G2211 (launched 2024) | | 29.7% |

Source: `results/national_trend.csv`.

## Practices by readiness tier

| Tier | Practices | Clinicians | Estimated QMB patients |
|---|---:|---:|---:|
| No visible care management | 21,809 | 29,205 | 793,785 |
| Visit-based services only | 23,980 | 101,484 | 2,459,800 |
| CCM or PCM only | 2,285 | 8,557 | 293,561 |
| Multi-service care management | 3,377 | 75,999 | 2,009,600 |

Source: `results/readiness_tiers.csv`. Large multi-site organizations dominate the multi-service tier because any site's billing counts for the whole organization.

## Equity

- **By dual-eligible share of the panel**, CCM or PCM billing is U-shaped: 9.2% of clinicians in the lowest fifth, 4.4% in the middle, 7.7% in the highest.
- **Where QMB patients are:** in the fifth of practices with the most dual-eligible patients, 25% of estimated QMB patients are with a practice showing no visible care management, against 9% in the fifth with the fewest.
- **Shortage areas:** 11.0% of dual-eligible patients in geographic primary care HPSA counties have a clinician billing CCM or PCM, against 12.9% elsewhere.

Sources: `results/equity.csv`, `results/readiness_by_dual_quintile.csv`.

## Payment

G0556 $16.37, G0557 $53.78 and G0558 $117.24 a month; base CCM (99490) $66.13. The median 2024 CCM biller billed 4.5 months per patient, $383 a year at 2026 rates. G0557 every month is $645; it pays more than observed CCM billing for 84% of CCM billers. Sources: `results/fee_schedule_2026.csv`, `results/ccm_vs_apcm_summary.csv`.

## National opportunity (traditional Medicare)

| Scenario | Allowed per year | Patient coinsurance |
|---|---:|---:|
| Low | $0.70B | $0.10B |
| Base | $3.06B | $0.43B |
| High | $8.27B | $1.18B |

Inputs in `seeds/apcm_scenarios.csv` and `docs/assumptions_log.md`. Source: `results/apcm_opportunity_national.csv`.

## Draft readiness score

Logistic model trained on G2211 uptake in 2024 from 2023 practice profiles: 47,564 practices, cross-validated AUROC 0.80. The least-ready tenth of practices holds 3.6 times the QMB patients its share of all patients would suggest. A check model on new CCM/PCM adoption has AUROC 0.74 and ranks practices similarly (Spearman 0.73). Source: `forecast/model_card_draft.json`, `forecast/qmb_by_readiness_decile.csv`.

## What the data cannot show

Patient-level APCM eligibility, consent, or same-month billing conflicts; Medicare Advantage; FQHC and RHC care billed under their own payment systems; and anything under CMS's 11-beneficiary suppression threshold. See `docs/data_validity_report.md`.
