-- How much of each code's national volume is invisible in the clinician-level file
-- because CMS drops clinician x code rows with fewer than 11 beneficiaries.
with visible as (
  select service_year, hcpcs, sum(services) as visible_services, count(distinct npi) as visible_clinicians
  from {{ ref('stg_mup_service') }}
  group by 1, 2
),
national as (
  select service_year, hcpcs, sum(services) as national_services, sum(clinicians) as national_clinician_rows,
         sum(benes) as national_benes_sum_over_settings
  from {{ ref('stg_mup_geography') }}
  where geo_level = 'National'
  group by 1, 2
)
select
  n.service_year,
  n.hcpcs,
  f.family,
  n.national_services,
  coalesce(v.visible_services, 0)                                      as visible_services,
  1 - coalesce(v.visible_services, 0) / nullif(n.national_services, 0) as invisible_service_share,
  n.national_clinician_rows,
  coalesce(v.visible_clinicians, 0)                                    as visible_clinicians,
  1 - coalesce(v.visible_clinicians, 0) / nullif(n.national_clinician_rows, 0) as invisible_clinician_share
from national n
left join visible v using (service_year, hcpcs)
left join {{ ref('code_families') }} f on f.code = n.hcpcs
