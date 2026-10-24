-- Share of dual-eligible enrollees who are QMBs (QMB-only plus QMB-plus), by county,
-- falling back to the state ratio when the county ratio is missing or unstable.
with base as (
  select enrollment_year, geo_level, state, fips,
         (qmb_only_benes + qmb_plus_benes) / nullif(dual_benes, 0) as qmb_share_of_duals,
         dual_benes
  from {{ ref('stg_enrollment') }}
  where geo_level in ('County', 'State')
)
select c.enrollment_year, c.fips as county_fips, c.state,
       case when c.dual_benes >= 100 and c.qmb_share_of_duals between 0 and 1
            then c.qmb_share_of_duals else s.qmb_share_of_duals end as qmb_share_of_duals,
       not (c.dual_benes >= 100 and c.qmb_share_of_duals between 0 and 1) as used_state_fallback,
       s.qmb_share_of_duals as state_qmb_share_of_duals
from base c
left join base s on s.geo_level = 'State' and s.state = c.state and s.enrollment_year = c.enrollment_year
where c.geo_level = 'County'
