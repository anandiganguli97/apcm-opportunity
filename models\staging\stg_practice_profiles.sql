{{ config(materialized='view') }}
select
  cast(practice_id as varchar) as practice_id,
  cast(practice_name as varchar) as practice_name,
  cast(rurality as varchar) as rurality,
  cast(shortage_area as boolean) as shortage_area,
  cast(dual_share as double) as dual_share,
  cast(ccm_months_per_100 as double) as ccm_months_per_100,
  cast(tcm_months_per_100 as double) as tcm_months_per_100,
  cast(bhi_months_per_100 as double) as bhi_months_per_100,
  cast(cocm_months_per_100 as double) as cocm_months_per_100,
  cast(attributed_beneficiaries as integer) as attributed_beneficiaries,
  cast(svi_percentile as double) as svi_percentile
from read_csv_auto('data/practice_profiles.csv', header=true)
