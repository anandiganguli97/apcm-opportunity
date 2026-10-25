-- How many primary care candidates the nursing-facility rule removes each year.
select
  service_year,
  count(*)                                                      as candidates,
  count(*) filter (where nursing_facility_focus)                as nursing_facility_focused,
  count(*) filter (where nursing_facility_focus and role = 'physician') as nursing_facility_focused_physicians,
  count(*) filter (where not nursing_facility_focus)            as primary_care_clinicians,
  sum(tot_benes) filter (where nursing_facility_focus)          as nursing_facility_focused_benes
from {{ ref('int_clinician_year_candidates') }}
group by 1
order by 1
