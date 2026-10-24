{{ config(materialized='view') }}
select
  cast(beneficiary_id as varchar) as beneficiary_id,
  cast(service_month as date) as service_month,
  date_part('year', cast(service_month as date))::integer as rate_year,
  cast(practice_id as varchar) as practice_id,
  greatest(0, cast(qualifying_chronic_count as integer)) as qualifying_chronic_count,
  cast(qmb_flag as boolean) as qmb_flag,
  cast(consent_proxy as boolean) as consent_proxy,
  cast(observed_care_mgmt_allowed_amount as double) as observed_care_mgmt_allowed_amount,
  cast(attribution_method as varchar) as attribution_method
from read_csv_auto('data/beneficiary_months.csv', header=true)
