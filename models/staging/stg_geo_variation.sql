-- Geographic Variation PUF (traditional Medicare), all-ages rows.
select
  cast(YEAR as integer)                                  as gv_year,
  BENE_GEO_LVL                                           as geo_level,
  BENE_GEO_DESC                                          as geo_desc,
  nullif(trim(BENE_GEO_CD), '')                          as geo_code,
  try_cast(BENES_TOTAL_CNT as double)                    as total_benes,
  try_cast(BENES_WTH_PTAPTB_CNT as double)               as benes_with_part_a_b,
  try_cast(BENES_OM_CNT as double)                       as original_medicare_benes,
  try_cast(BENES_MA_CNT as double)                       as ma_benes,
  try_cast(MA_PRTCPTN_RATE as double)                    as ma_participation_rate,
  try_cast(BENE_DUAL_PCT as double)                      as dual_pct
from read_parquet('{{ var("processed_dir") }}/geo_variation.parquet')
