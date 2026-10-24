-- Published / total practice denominators must reconcile to source people.
with source_counts as (
 select practice_id, count(distinct beneficiary_id) as people
 from {{ ref('stg_beneficiary_months') }} group by practice_id
)
select p.practice_id
from {{ ref('stg_practice_profiles') }} p join source_counts s using (practice_id)
where p.attributed_beneficiaries < s.people
