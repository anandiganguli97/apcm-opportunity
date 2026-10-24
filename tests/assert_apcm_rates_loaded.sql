-- All three APCM base codes must have a 2026 non-facility rate.
select code from (values ('G0556'), ('G0557'), ('G0558')) t(code)
where code not in (select hcpcs from {{ ref('stg_pfs_rates') }} where cf_type = 'nonqpp' and national_nonfac_amount > 0)
