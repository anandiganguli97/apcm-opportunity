-- Each beneficiary-month must map to exactly one tier and practice.
select beneficiary_id, service_month
from {{ ref('int_beneficiary_month_tier') }}
group by beneficiary_id, service_month
having count(*) <> 1
