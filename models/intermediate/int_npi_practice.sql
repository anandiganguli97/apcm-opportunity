-- Assign each clinician to one group practice from the current Doctors and Clinicians
-- file. Many clinicians are listed with several organizations. Some organizations,
-- notably national therapy companies, list thousands of physicians who nearly all
-- practice in another group. The practice is the organization with the highest share of
-- members listed with no other organization, then the one the NPI is listed with most
-- often, then the larger organization, then lowest ID. Clinicians with no organization
-- are their own practice.
with orgs_per_npi as (
  select npi, count(distinct org_pac_id) as n_orgs
  from {{ ref('stg_dac') }}
  where org_pac_id is not null
  group by 1
),
org_mix as (
  select d.org_pac_id,
         avg(case when o.n_orgs = 1 then 1.0 else 0.0 end) as org_exclusive_share
  from (select distinct npi, org_pac_id from {{ ref('stg_dac') }} where org_pac_id is not null) d
  join orgs_per_npi o using (npi)
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
  select c.*, m.org_exclusive_share,
         row_number() over (partition by c.npi order by m.org_exclusive_share desc,
                            c.listings desc, c.org_members desc nulls last, c.org_pac_id) as rk
  from counts c join org_mix m using (org_pac_id)
)
select npi, org_pac_id, facility_name, org_members, org_exclusive_share
from ranked where rk = 1
