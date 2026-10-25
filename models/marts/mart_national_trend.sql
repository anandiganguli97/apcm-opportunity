-- Primary care care-management billing, 2019-2024, from the clinician-level file.
with c as (select * from {{ ref('int_clinician_year') }})
select
  service_year,
  count(*)                                                        as pcp_clinicians,
  count(*) filter (where role = 'physician')                      as pcp_physicians,
  sum(tot_benes)                                                  as pcp_benes_sum,
  avg(has_ccm::int)                                               as share_billing_ccm,
  avg(has_pcm::int)                                               as share_billing_pcm,
  avg(has_established_care_mgmt::int)                             as share_billing_ccm_or_pcm,
  avg(has_tcm::int)                                               as share_billing_tcm,
  avg(has_bhi_or_cocm::int)                                       as share_billing_bhi_or_cocm,
  avg(has_rpm::int)                                               as share_billing_rpm,
  avg(has_awv::int)                                               as share_billing_awv,
  avg(has_acp::int)                                               as share_billing_acp,
  avg((coalesce(g2211_benes_min, 0) > 0)::int)                    as share_billing_g2211,
  avg((coalesce(sdoh_nav_benes_min, 0) > 0)::int)                 as share_billing_sdoh_navigation,
  100.0 * sum(ccm_patient_months) / nullif(sum(tot_benes), 0)     as ccm_patient_months_per_100_benes,
  sum(ccm_allowed)                                                as ccm_allowed_visible
from c
group by 1
order by 1
