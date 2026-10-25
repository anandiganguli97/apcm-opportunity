-- How many primary care candidates the office-based rule removes each year, and why.
select
  service_year,
  count(*)                                                                    as candidates,
  count(*) filter (where not_office_based)                                    as excluded,
  count(*) filter (where not_office_based and no_visible_office_visits)       as excluded_no_visible_office_visits,
  count(*) filter (where not_office_based and not no_visible_office_visits)   as excluded_mainly_facility_or_home_visits,
  count(*) filter (where not_office_based and role = 'physician')             as excluded_physicians,
  count(*) filter (where not not_office_based)                                as primary_care_clinicians,
  sum(tot_benes) filter (where not_office_based)                              as excluded_benes
from {{ ref('int_clinician_year_candidates') }}
group by 1
order by 1
