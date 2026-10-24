-- Visible billing per clinician, service year and code family.
-- benes_min is the largest beneficiary count on any single code in the family:
-- a conservative floor on unique patients (patients can appear under several codes).
-- base_services counts first-unit monthly codes, which equal patient-months for CCM/PCM.
select
  service_year,
  npi,
  family,
  max(benes)                                                     as benes_min,
  sum(services)                                                  as services,
  sum(services) filter (where hcpcs in ('99490','99491','99487','99424','99426','G2064','G2065',
                                        '99484','99492','99493','G2214','99457'))     as base_services,
  sum(allowed_amt)                                               as allowed_amt,
  count(distinct hcpcs)                                          as codes_billed
from {{ ref('stg_mup_service') }}
where family is not null
group by 1, 2, 3
