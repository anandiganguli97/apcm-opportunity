-- National APCM opportunity anchored on the count of traditional Medicare beneficiaries
-- (Geographic Variation PUF) and the QMB share of primary care patients (clinician
-- dual counts x county QMB-to-dual ratios). Scenario parameters: seeds/apcm_scenarios.csv.
-- QMBs owe no Medicare cost sharing; everyone else is modeled at 20% coinsurance.
with ffs as (
  select original_medicare_benes as ffs_benes
  from {{ ref('stg_geo_variation') }}
  where geo_level = 'National' and gv_year = {{ var('analysis_year') }}
),
mix as (
  select sum(est_qmb_patients) / nullif(sum(tot_benes) filter (where est_qmb_patients is not null), 0) as qmb_share
  from {{ ref('mart_clinician') }}
),
rates as (
  select
    max(national_nonfac_amount) filter (where hcpcs = 'G0556' and cf_type = 'nonqpp') as r556,
    max(national_nonfac_amount) filter (where hcpcs = 'G0557' and cf_type = 'nonqpp') as r557,
    max(national_nonfac_amount) filter (where hcpcs = 'G0558' and cf_type = 'nonqpp') as r558
  from {{ ref('stg_pfs_rates') }}
),
months as (
  select s.scenario, s.capture_rate, s.consent_rate, s.share_2plus_qmb, s.share_2plus_non_qmb,
    f.ffs_benes, m.qmb_share, r.r556, r.r557, r.r558,
    12 * f.ffs_benes * m.qmb_share * s.share_2plus_qmb                   as g0558_months,
    12 * f.ffs_benes * m.qmb_share * (1 - s.share_2plus_qmb)             as g0556_qmb_months,
    12 * f.ffs_benes * (1 - m.qmb_share) * s.share_2plus_non_qmb         as g0557_months,
    12 * f.ffs_benes * (1 - m.qmb_share) * (1 - s.share_2plus_non_qmb)   as g0556_nonqmb_months
  from {{ ref('apcm_scenarios') }} s cross join ffs f cross join mix m cross join rates r
)
select
  scenario, ffs_benes, qmb_share, share_2plus_qmb, share_2plus_non_qmb, capture_rate, consent_rate,
  r556, r557, r558,
  g0556_qmb_months + g0556_nonqmb_months                                         as g0556_months,
  g0557_months,
  g0558_months,
  (g0556_qmb_months + g0556_nonqmb_months) * r556 + g0557_months * r557 + g0558_months * r558 as allowed_full_capture,
  ((g0556_qmb_months + g0556_nonqmb_months) * r556 + g0557_months * r557 + g0558_months * r558)
    * capture_rate * consent_rate                                                as allowed_scenario,
  0.20 * (g0556_nonqmb_months * r556 + g0557_months * r557) * capture_rate * consent_rate as patient_coinsurance_scenario
from months
