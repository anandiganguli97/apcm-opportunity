-- Assign each clinician to one group practice from the current Doctors and Clinicians
-- file. Many clinicians are listed with several organizations, often including national
-- therapy or post-acute companies with thousands of members. The practice is the
-- organization with the highest share of primary care clinicians among its members, then
-- the one the NPI is listed with most often, then the larger organization, then lowest ID.
-- Clinicians with no organization are their own practice.
with pc_specs as (
  select upper(provider_type) as spec from {{ ref('primary_care_specialties') }}
),
org_mix as (
  select org_pac_id,
         count(distinct npi) as org_npis,
         count(distinct case when upper(primary_specialty) in (select spec from pc_specs) then npi end) as org_pc_npis
  from {{ ref('stg_dac') }}
  where org_pac_id is not null
  group by 1
),
counts as (
  select npi, org_pac_id, max(facility_name) as facility_name, max(org_members) as org_members,
         count(*) as listings
  from {{ ref('stg_dac') }}
  where org_pac_id is not null
  group by 1, 2
),
ranked as (
  select c.*, m.org_pc_npis::double / nullif(m.org_npis, 0) as org_primary_care_share,
         row_number() over (partition by c.npi order by m.org_pc_npis::double / nullif(m.org_npis, 0) desc nulls last,
                            c.listings desc, c.org_members desc nulls last, c.org_pac_id) as rk
  from counts c join org_mix m using (org_pac_id)
)
select npi, org_pac_id, facility_name, org_members, org_primary_care_share
from ranked where rk = 1
