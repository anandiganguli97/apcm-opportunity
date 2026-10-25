-- Primary care clinicians by service year: candidates from int_clinician_year_candidates
-- that are office-based (visible office visits, not outnumbered by nursing facility and
-- home/residence visits). Post-acute, long-term care and home-visit groups are excluded.
select * exclude (no_visible_office_visits, not_office_based)
from {{ ref('int_clinician_year_candidates') }}
where not not_office_based
