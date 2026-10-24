-- Medicare Monthly Enrollment, annual rows. Counts include Medicare Advantage enrollees.
select
  cast(YEAR as integer)                                  as enrollment_year,
  BENE_GEO_LVL                                           as geo_level,
  BENE_STATE_ABRVTN                                      as state,
  nullif(trim(BENE_FIPS_CD), '')                         as fips,
  try_cast(TOT_BENES as double)                          as total_benes,
  try_cast(ORGNL_MDCR_BENES as double)                   as original_medicare_benes,
  try_cast(DUAL_TOT_BENES as double)                     as dual_benes,
  try_cast(QMB_ONLY_BENES as double)                     as qmb_only_benes,
  try_cast(QMB_PLUS_BENES as double)                     as qmb_plus_benes
from read_parquet('{{ var("processed_dir") }}/monthly_enrollment.parquet')
