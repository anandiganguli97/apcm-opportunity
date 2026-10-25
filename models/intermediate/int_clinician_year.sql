-- Primary care clinicians by service year: candidates from int_clinician_year_candidates,
-- excluding clinicians whose visible work is mainly nursing facility visits (post-acute
-- and long-term care groups rather than office-based primary care).
select * exclude (nursing_facility_focus)
from {{ ref('int_clinician_year_candidates') }}
where not nursing_facility_focus
