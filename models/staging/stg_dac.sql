-- Doctors and Clinicians national file (current snapshot): clinician to group practice.
select
  npi,
  nullif(trim(org_pac_id), '')                           as org_pac_id,
  try_cast(num_org_mem as integer)                       as org_members,
  pri_spec                                               as primary_specialty,
  facility_name,
  state,
  left(zip, 5)                                           as zip5
from read_parquet('{{ var("processed_dir") }}/dac.parquet')
