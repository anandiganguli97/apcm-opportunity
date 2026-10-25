-- For clinicians billing CCM in the analysis year: annual revenue per CCM patient at
-- 2026 national rates under their observed CCM pattern, versus APCM level 2 (G0557)
-- billed in the same months, or in all 12 months. CCM requires 20+ minutes of care
-- management time per month; APCM has no monthly time threshold.
with svc as (
  select s.npi, s.hcpcs, sum(s.services) as services
  from {{ ref('stg_mup_service') }} s
  where s.service_year = {{ var('analysis_year') }} and s.family = 'CCM'
  group by 1, 2
),
rates as (
  select hcpcs, national_nonfac_amount as rate
  from {{ ref('stg_pfs_rates') }} where cf_type = 'nonqpp'
),
rev as (
  select svc.npi, sum(svc.services * r.rate) as ccm_revenue_2026_rates
  from svc join rates r using (hcpcs)
  group by 1
),
c as (
  select * from {{ ref('mart_clinician') }} where has_ccm and ccm_benes_min > 0 and ccm_patient_months > 0
)
select
  c.npi, c.practice_id, c.provider_type, c.state, c.rurality,
  c.ccm_benes_min                                                    as ccm_patients_min,
  c.ccm_patient_months / c.ccm_benes_min                             as ccm_months_per_patient,
  rev.ccm_revenue_2026_rates / c.ccm_benes_min                       as ccm_revenue_per_patient_year,
  (c.ccm_patient_months / c.ccm_benes_min) * g.rate                  as apcm_g0557_same_months,
  12 * g.rate                                                        as apcm_g0557_twelve_months,
  rev.ccm_revenue_2026_rates / c.ccm_benes_min - (c.ccm_patient_months / c.ccm_benes_min) * g.rate as ccm_minus_apcm_same_months
from c
join rev on rev.npi = c.npi
cross join (select rate from rates where hcpcs = 'G0557') g
