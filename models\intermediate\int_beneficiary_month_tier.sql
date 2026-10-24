{{ config(materialized='table') }}
with tiered as (
  select *,
    case when qmb_flag and qualifying_chronic_count >= 2 then 'G0558'
         when qualifying_chronic_count >= 2 then 'G0557'
         else 'G0556' end as apcm_code,
    case when qmb_flag and qualifying_chronic_count >= 2 then true else false end as is_qmb_tier
  from {{ ref('stg_beneficiary_months') }}
), priced as (
  select t.*, cast(r.monthly_allowed_amount as double) as monthly_allowed_amount,
         r.source_status as rate_source_status
  from tiered t
  left join {{ ref('apcm_rates') }} r
    on t.rate_year = cast(r.rate_year as integer) and t.apcm_code = r.code
)
select *,
  monthly_allowed_amount * 0.20 * case when qmb_flag then 0 else 1 end as modeled_coinsurance,
  observed_care_mgmt_allowed_amount > 0 as has_observed_overlap_candidate,
  case when observed_care_mgmt_allowed_amount > 0
       then observed_care_mgmt_allowed_amount else 0 end as possible_displaced_allowed_amount
from priced

