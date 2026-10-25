-- National and state totals by HCPCS code (used to measure what suppression hides).
with src as (
  select * from read_parquet('{{ var("processed_dir") }}/mup_geo_*.parquet', union_by_name = true)
)
select
  cast(service_year as integer)                          as service_year,
  Rndrng_Prvdr_Geo_Lvl                                   as geo_level,
  Rndrng_Prvdr_Geo_Cd                                    as geo_code,
  Rndrng_Prvdr_Geo_Desc                                  as geo_desc,
  HCPCS_Cd                                               as hcpcs,
  Place_Of_Srvc                                          as place_of_service,
  try_cast(Tot_Rndrng_Prvdrs as integer)                 as clinicians,
  try_cast(Tot_Benes as bigint)                          as benes,
  try_cast(Tot_Srvcs as double)                          as services,
  try_cast(Avg_Mdcr_Alowd_Amt as double) * try_cast(Tot_Srvcs as double) as allowed_amt
from src
