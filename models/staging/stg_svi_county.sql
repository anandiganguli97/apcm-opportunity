-- CDC/ATSDR Social Vulnerability Index 2022 (overall percentile rank; -999 = missing).
select
  lpad(county_fips, 5, '0')                              as county_fips,
  state,
  county,
  case when try_cast(svi_overall as double) < 0 then null
       else try_cast(svi_overall as double) end          as svi_overall
from read_parquet('{{ var("processed_dir") }}/svi_county.parquet')
