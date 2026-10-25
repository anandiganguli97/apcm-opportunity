-- Primary care clinicians by service year, with patient mix and visible care
-- management billing. Definition of primary care lives in seeds/primary_care_specialties.csv.
with fam as (
  select * from {{ ref('int_npi_family_year') }}
),
pv as (
  select
    service_year, npi,
    max(case when family = 'CCM'  then benes_min end)              as ccm_benes_min,
    sum(case when family = 'CCM'  then base_services end)          as ccm_patient_months,
    sum(case when family = 'CCM'  then allowed_amt end)            as ccm_allowed,
    max(case when family = 'PCM'  then benes_min end)              as pcm_benes_min,
    sum(case when family = 'PCM'  then base_services end)          as pcm_patient_months,
    max(case when family = 'TCM'  then benes_min end)              as tcm_benes_min,
    sum(case when family = 'TCM'  then services end)               as tcm_services,
    max(case when family = 'BHI'  then benes_min end)              as bhi_benes_min,
    max(case when family = 'COCM' then benes_min end)              as cocm_benes_min,
    max(case when family = 'RPM'  then benes_min end)              as rpm_benes_min,
    max(case when family = 'AWV'  then benes_min end)              as awv_benes_min,
    sum(case when family = 'AWV'  then services end)               as awv_services,
    max(case when family = 'ACP'  then benes_min end)              as acp_benes_min,
    max(case when family = 'COMPLEXITY_ADDON' then benes_min end)  as g2211_benes_min,
    max(case when family = 'SDOH_NAVIGATION' then benes_min end)   as sdoh_nav_benes_min,
    sum(case when family = 'OFFICE_EM' then services end)          as office_em_services,
    max(case when family = 'APCM' then benes_min end)              as apcm_benes_min,
    sum(case when family in ('CCM','PCM','TCM','BHI','COCM','RPM','ACP') then allowed_amt end) as care_mgmt_allowed
  from fam
  group by 1, 2
),
prov as (
  select p.*, s.role
  from {{ ref('stg_mup_provider') }} p
  join {{ ref('primary_care_specialties') }} s on s.provider_type = p.provider_type
  where p.entity_code = 'I'
)
select
  prov.service_year,
  prov.npi,
  prov.provider_type,
  prov.role,
  prov.state,
  prov.zip5,
  z.county_fips,
  prov.ruca,
  case when prov.ruca is null then 'Unknown'
       when floor(prov.ruca) <= 3 then 'Metropolitan'
       when floor(prov.ruca) <= 6 then 'Micropolitan'
       when floor(prov.ruca) <= 9 then 'Small town'
       else 'Rural' end                                              as rurality,
  prov.tot_benes,
  -- dual count: reported value, else total minus reported non-dual
  coalesce(prov.dual_cnt_reported,
           case when prov.nondual_cnt_reported is not null
                then prov.tot_benes - prov.nondual_cnt_reported end) as dual_cnt,
  prov.dual_cnt_reported is null                                     as dual_cnt_derived_or_missing,
  prov.avg_hcc_risk_score,
  prov.mean_ccw_conditions,
  pv.* exclude (service_year, npi),
  coalesce(pv.ccm_benes_min, 0) > 0                               as has_ccm,
  coalesce(pv.pcm_benes_min, 0) > 0                               as has_pcm,
  coalesce(pv.tcm_benes_min, 0) > 0                               as has_tcm,
  coalesce(pv.bhi_benes_min, 0) + coalesce(pv.cocm_benes_min, 0) > 0 as has_bhi_or_cocm,
  coalesce(pv.rpm_benes_min, 0) > 0                               as has_rpm,
  coalesce(pv.awv_benes_min, 0) > 0                               as has_awv,
  coalesce(pv.acp_benes_min, 0) > 0                               as has_acp,
  coalesce(pv.ccm_benes_min, 0) + coalesce(pv.pcm_benes_min, 0) > 0 as has_established_care_mgmt
from prov
left join pv on pv.service_year = prov.service_year and pv.npi = prov.npi
left join {{ ref('stg_zip_county') }} z on z.zip5 = prov.zip5
where prov.role = 'physician'
   or coalesce(pv.awv_benes_min, 0) > 0   -- NPs and PAs count as primary care only with visible AWV billing
