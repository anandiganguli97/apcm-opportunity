-- Denominator shares and monetary inputs must be in valid ranges.
select practice_id from {{ ref('stg_practice_profiles') }}
where dual_share < 0 or dual_share > 1 or svi_percentile < 0 or svi_percentile > 1
   or attributed_beneficiaries < 0
union all
select practice_id from {{ ref('stg_practice_profiles') }}
where ccm_months_per_100 < 0 or tcm_months_per_100 < 0
   or bhi_months_per_100 < 0 or cocm_months_per_100 < 0
