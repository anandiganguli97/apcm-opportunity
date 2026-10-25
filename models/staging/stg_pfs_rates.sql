-- National physician fee schedule amounts for the codes in seeds/code_families.csv.
-- Non-facility amount = non-facility total RVUs x conversion factor (no geographic adjustment).
select
  {{ var("fee_schedule_year") }}                         as fee_year,
  r.hcpcs,
  f.family,
  r.description,
  r.status_code,
  r.cf_type,
  try_cast(r.work_rvu as double)                         as work_rvu,
  try_cast(r.nonfac_pe_rvu as double)                    as nonfac_pe_rvu,
  try_cast(r.mp_rvu as double)                           as mp_rvu,
  try_cast(r.nonfac_total_rvu as double)                 as nonfac_total_rvu,
  try_cast(r.fac_total_rvu as double)                    as fac_total_rvu,
  try_cast(r.conversion_factor as double)                as conversion_factor,
  round(try_cast(r.nonfac_total_rvu as double) * try_cast(r.conversion_factor as double), 2) as national_nonfac_amount,
  round(try_cast(r.fac_total_rvu as double) * try_cast(r.conversion_factor as double), 2)    as national_fac_amount
from read_parquet('{{ var("processed_dir") }}/pfs_rvu.parquet') r
join {{ ref('code_families') }} f on f.code = r.hcpcs
where r.modifier = ''
