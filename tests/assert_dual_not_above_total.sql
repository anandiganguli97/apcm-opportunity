-- A clinician's dual-eligible count can never exceed their total beneficiaries.
select npi, service_year, dual_cnt, tot_benes
from {{ ref('int_clinician_year') }}
where dual_cnt > tot_benes
