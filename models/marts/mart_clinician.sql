-- Analysis-year primary care clinicians with practice, geography and equity attributes.
with c as (
  select * from {{ ref('int_clinician_year') }} where service_year = {{ var('analysis_year') }}
)
select
  c.*,
  coalesce(p.org_pac_id, 'npi:' || c.npi)                          as practice_id,
  p.facility_name                                                   as practice_name,
  p.org_members                                                     as practice_enrolled_members,
  c.dual_cnt::double / nullif(c.tot_benes, 0)                       as dual_share,
  q.qmb_share_of_duals,
  c.dual_cnt * q.qmb_share_of_duals                                 as est_qmb_patients,
  coalesce(h.has_geographic_pc_hpsa, false)                         as county_geographic_pc_hpsa,
  coalesce(h.has_any_pc_hpsa, false)                                as county_any_pc_hpsa,
  s.svi_overall
from c
left join {{ ref('int_npi_practice') }} p on p.npi = c.npi
left join {{ ref('int_county_qmb_ratio') }} q
       on q.county_fips = c.county_fips and q.enrollment_year = c.service_year
left join {{ ref('stg_hpsa_county') }} h on h.county_fips = c.county_fips
left join {{ ref('stg_svi_county') }} s on s.county_fips = c.county_fips
