-- Assign each clinician to one group practice from the current Doctors and Clinicians
-- file: the organization listed most often for that NPI, ties broken by larger
-- organization size, then lowest ID. Clinicians with no organization are their own practice.
with counts as (
  select npi, org_pac_id, max(facility_name) as facility_name, max(org_members) as org_members,
         count(*) as listings
  from {{ ref('stg_dac') }}
  where org_pac_id is not null
  group by 1, 2
),
ranked as (
  select *, row_number() over (partition by npi order by listings desc, org_members desc nulls last, org_pac_id) as rk
  from counts
)
select npi, org_pac_id, facility_name, org_members
from ranked where rk = 1
