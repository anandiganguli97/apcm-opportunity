-- 2020 ZCTA assigned to the county holding most of its land area. ZIP codes are
-- treated as ZCTAs; ZIPs without a ZCTA (PO boxes, unique ZIPs) stay unmatched.
select zcta as zip5, county_fips, land_share
from read_parquet('{{ var("processed_dir") }}/zcta_county.parquet')
