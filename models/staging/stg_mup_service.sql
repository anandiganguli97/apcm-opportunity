-- Clinician x HCPCS x place of service rows for the care management, preventive,
-- APCM and office visit codes in pipeline/hcpcs_codes.json. Rows for fewer than
-- 11 beneficiaries are absent from the public file (not zero).
with src as (
  select * from read_parquet('{{ var("processed_dir") }}/mup_svc_*.parquet', union_by_name = true)
)
select
  cast(s.service_year as integer)                        as service_year,
  s.Rndrng_NPI                                           as npi,
  s.Rndrng_Prvdr_Type                                    as provider_type,
  s.HCPCS_Cd                                             as hcpcs,
  f.family,
  s.Place_Of_Srvc                                        as place_of_service,
  try_cast(s.Tot_Benes as integer)                       as benes,
  try_cast(s.Tot_Srvcs as double)                        as services,
  try_cast(s.Avg_Mdcr_Alowd_Amt as double) * try_cast(s.Tot_Srvcs as double) as allowed_amt,
  try_cast(s.Avg_Mdcr_Pymt_Amt as double)  * try_cast(s.Tot_Srvcs as double) as medicare_paid_amt
from src s
left join {{ ref('code_families') }} f on f.code = s.HCPCS_Cd
