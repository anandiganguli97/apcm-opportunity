-- Care management readiness across equity dimensions, analysis year.
-- clinician_share: share of primary care clinicians in the group with visible CCM or PCM.
-- dual_patient_share / nondual_patient_share: share of dual (non-dual) patients whose
-- clinician bills CCM or PCM. Patients seeing several clinicians count more than once.
with c as (
  select *,
    ntile(5) over (order by dual_share, npi) as dual_share_quintile
  from {{ ref('mart_clinician') }}
  where dual_share is not null
),
labelled as (
  select 'Dual-eligible share of panel (quintile)' as dimension,
         'Q' || dual_share_quintile || case dual_share_quintile when 1 then ' (lowest)' when 5 then ' (highest)' else '' end as grp,
         * from c
  union all select 'Rurality (clinician ZIP, RUCA)', rurality, * from c
  union all select 'County primary care shortage area', case when county_geographic_pc_hpsa then 'Geographic HPSA county' else 'Not a geographic HPSA county' end, * from c
  union all select 'Social Vulnerability Index (county quartile)',
         case when svi_overall is null then 'Unknown' when svi_overall < 0.25 then 'Q1 (least vulnerable)'
              when svi_overall < 0.5 then 'Q2' when svi_overall < 0.75 then 'Q3' else 'Q4 (most vulnerable)' end, * from c
  union all select 'All primary care clinicians', 'All', * from c
)
select
  dimension,
  grp,
  count(*)                                                                   as clinicians,
  avg(dual_share)                                                            as mean_dual_share,
  avg(has_established_care_mgmt::int)                                        as clinician_share_ccm_or_pcm,
  avg(has_ccm::int)                                                          as clinician_share_ccm,
  avg(has_tcm::int)                                                          as clinician_share_tcm,
  avg(has_bhi_or_cocm::int)                                                  as clinician_share_bhi_or_cocm,
  sum(dual_cnt) filter (where has_established_care_mgmt) / nullif(sum(dual_cnt), 0)                      as dual_patient_share_with_ccm_or_pcm,
  sum(tot_benes - dual_cnt) filter (where has_established_care_mgmt) / nullif(sum(tot_benes - dual_cnt), 0) as nondual_patient_share_with_ccm_or_pcm,
  sum(est_qmb_patients) filter (where has_established_care_mgmt) / nullif(sum(est_qmb_patients), 0)     as est_qmb_patient_share_with_ccm_or_pcm,
  100.0 * sum(ccm_patient_months) / nullif(sum(tot_benes), 0)                as ccm_patient_months_per_100_benes
from labelled
group by 1, 2
order by 1, 2
