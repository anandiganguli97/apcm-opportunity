-- Counties containing at least one designated primary care HPSA, by designation type.
select
  lpad(county_fips, 5, '0')                              as county_fips,
  bool_or(designation_type in ('Geographic HPSA', 'High Needs Geographic HPSA')) as has_geographic_pc_hpsa,
  bool_or(true)                                          as has_any_pc_hpsa,
  max(try_cast(hpsa_score as integer))                   as max_hpsa_score
from read_parquet('{{ var("processed_dir") }}/hpsa_pc.parquet')
where hpsa_status = 'Designated'
  and county_fips is not null and county_fips <> ''
group by 1
