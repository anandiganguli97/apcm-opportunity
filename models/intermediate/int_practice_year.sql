-- Primary care practices by service year: readiness features and visible billing of
-- newly launched codes. Practice membership comes from the current Doctors and
-- Clinicians snapshot for every year (CMS publishes no historical snapshots).
with c as (
  select c.*, coalesce(p.org_pac_id, 'npi:' || c.npi) as practice_id
  from {{ ref('int_clinician_year') }} c
  left join {{ ref('int_npi_practice') }} p on p.npi = c.npi
)
select
  service_year,
  practice_id,
  count(*)                                                        as pcp_clinicians,
  avg((role = 'physician')::int)                                  as physician_share,
  sum(tot_benes)                                                  as patient_panel_proxy,
  sum(dual_cnt)::double / nullif(sum(tot_benes) filter (where dual_cnt is not null), 0) as dual_share,
  sum(tot_benes * avg_hcc_risk_score) / nullif(sum(tot_benes) filter (where avg_hcc_risk_score is not null), 0) as avg_hcc_risk_score,
  avg(case when rurality = 'Metropolitan' then 1.0 when rurality = 'Unknown' then null else 0.0 end) as metro_share,
  bool_or(has_ccm)                                                as has_ccm,
  bool_or(has_pcm)                                                as has_pcm,
  bool_or(has_tcm)                                                as has_tcm,
  bool_or(has_bhi_or_cocm)                                        as has_bhi_or_cocm,
  bool_or(has_rpm)                                                as has_rpm,
  bool_or(has_acp)                                                as has_acp,
  avg(has_awv::int)                                               as awv_clinician_share,
  bool_or(has_established_care_mgmt)                              as has_established_care_mgmt,
  bool_or(coalesce(g2211_benes_min, 0) > 0)                       as has_g2211,
  bool_or(coalesce(apcm_benes_min, 0) > 0)                        as has_apcm,
  sum(office_em_services) / nullif(sum(tot_benes), 0)             as office_em_per_bene,
  100.0 * sum(ccm_patient_months) / nullif(sum(tot_benes), 0)     as ccm_months_per_100_benes
from c
group by 1, 2
