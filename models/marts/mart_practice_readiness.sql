{{ config(materialized='table') }}
with signals as (
 select *,
   ccm_months_per_100 + tcm_months_per_100 + bhi_months_per_100 + cocm_months_per_100 as care_mgmt_signal_per_100
 from {{ ref('stg_practice_profiles') }}
), scored as (
 select *,
   least(100.0, care_mgmt_signal_per_100 * 2.0) as billing_readiness_score,
   case when dual_share >= 0.25 then 'high_dual_share'
        when dual_share >= 0.15 then 'medium_dual_share'
        else 'low_dual_share' end as dual_share_band
 from signals
)
select * from scored
