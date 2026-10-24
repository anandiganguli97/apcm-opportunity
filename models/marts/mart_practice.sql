-- Analysis-year primary care practices (group practice or solo clinician), with
-- readiness signals, patient mix and base-scenario APCM opportunity.
-- Patient counts are summed across clinicians and can double count shared patients.
with c as (select * from {{ ref('mart_clinician') }}),
lead_clinician as (
  select practice_id, state, county_fips, rurality, county_geographic_pc_hpsa, svi_overall
  from (select *, row_number() over (partition by practice_id order by tot_benes desc, npi) rk from c)
  where rk = 1
),
agg as (
  select
    practice_id,
    max(practice_name)                                             as practice_name,
    count(*)                                                       as pcp_clinicians,
    count(*) filter (where role = 'physician')                     as pcp_physicians,
    sum(tot_benes)                                                 as patient_panel_proxy,
    sum(dual_cnt)                                                  as dual_patients,
    sum(est_qmb_patients)                                          as est_qmb_patients,
    sum(dual_cnt)::double / nullif(sum(tot_benes) filter (where dual_cnt is not null), 0) as dual_share,
    sum(tot_benes * avg_hcc_risk_score) / nullif(sum(tot_benes) filter (where avg_hcc_risk_score is not null), 0) as avg_hcc_risk_score,
    bool_or(has_ccm)                                               as has_ccm,
    bool_or(has_pcm)                                               as has_pcm,
    bool_or(has_tcm)                                               as has_tcm,
    bool_or(has_bhi_or_cocm)                                       as has_bhi_or_cocm,
    bool_or(has_rpm)                                               as has_rpm,
    bool_or(has_awv)                                               as has_awv,
    bool_or(has_acp)                                               as has_acp,
    bool_or(coalesce(g2211_benes_min, 0) > 0)                      as has_g2211,
    bool_or(has_established_care_mgmt)                             as has_established_care_mgmt,
    sum(ccm_patient_months)                                        as ccm_patient_months,
    sum(care_mgmt_allowed)                                         as care_mgmt_allowed_visible
  from c
  group by 1
),
rates as (
  select
    max(national_nonfac_amount) filter (where hcpcs = 'G0556' and cf_type = 'nonqpp') as r556,
    max(national_nonfac_amount) filter (where hcpcs = 'G0557' and cf_type = 'nonqpp') as r557,
    max(national_nonfac_amount) filter (where hcpcs = 'G0558' and cf_type = 'nonqpp') as r558
  from {{ ref('stg_pfs_rates') }}
),
sc as (select * from {{ ref('apcm_scenarios') }} where scenario = 'base')
select
  a.*,
  l.state, l.county_fips, l.rurality, l.county_geographic_pc_hpsa, l.svi_overall,
  case when a.has_established_care_mgmt and (a.has_bhi_or_cocm or a.has_rpm or a.has_tcm) then '3 Multi-service care management'
       when a.has_established_care_mgmt then '2 CCM or PCM'
       when a.has_tcm or a.has_acp or a.has_awv then '1 Visit-based services only'
       else '0 No visible care management' end                     as readiness_tier,
  -- base-scenario full-year APCM allowed amount at 2026 national non-facility rates,
  -- before capture and consent (patient_panel_proxy can double count shared patients)
  12 * (
      coalesce(a.est_qmb_patients, 0) * (sc.share_2plus_qmb * r.r558 + (1 - sc.share_2plus_qmb) * r.r556)
    + greatest(a.patient_panel_proxy - coalesce(a.est_qmb_patients, 0), 0)
        * (sc.share_2plus_non_qmb * r.r557 + (1 - sc.share_2plus_non_qmb) * r.r556)
  )                                                                  as apcm_allowed_full_capture_base,
  12 * (
      coalesce(a.est_qmb_patients, 0) * (sc.share_2plus_qmb * r.r558 + (1 - sc.share_2plus_qmb) * r.r556)
    + greatest(a.patient_panel_proxy - coalesce(a.est_qmb_patients, 0), 0)
        * (sc.share_2plus_non_qmb * r.r557 + (1 - sc.share_2plus_non_qmb) * r.r556)
  ) * sc.capture_rate * sc.consent_rate                              as apcm_allowed_base_scenario
from agg a
left join lead_clinician l using (practice_id)
cross join rates r
cross join sc
