-- One row per clinician (NPI) per service year from the CMS by-Provider file.
-- CMS blanks counts derived from fewer than 11 beneficiaries; those stay NULL.
with src as (
  select * from read_parquet('{{ var("processed_dir") }}/mup_prov_*.parquet', union_by_name = true)
)
select
  cast(service_year as integer)                         as service_year,
  Rndrng_NPI                                            as npi,
  Rndrng_Prvdr_Ent_Cd                                   as entity_code,
  Rndrng_Prvdr_Type                                     as provider_type,
  Rndrng_Prvdr_State_Abrvtn                             as state,
  Rndrng_Prvdr_State_FIPS                               as state_fips,
  lpad(Rndrng_Prvdr_Zip5, 5, '0')                       as zip5,
  try_cast(Rndrng_Prvdr_RUCA as double)                 as ruca,
  Rndrng_Prvdr_Mdcr_Prtcptg_Ind                         as medicare_participating,
  try_cast(Tot_Benes as integer)                        as tot_benes,
  try_cast(Tot_Srvcs as double)                         as tot_srvcs,
  try_cast(Tot_Mdcr_Alowd_Amt as double)                as tot_allowed,
  try_cast(Bene_Dual_Cnt as integer)                    as dual_cnt_reported,
  try_cast(Bene_Ndual_Cnt as integer)                   as nondual_cnt_reported,
  try_cast(Bene_Avg_Risk_Scre as double)                as avg_hcc_risk_score,
  try_cast(Bene_Avg_Age as double)                      as avg_age,
  -- mean number of the 25 CCW conditions reported per beneficiary (NULL if any field is blank)
  (  try_cast(Bene_CC_BH_ADHD_OthCD_V1_Pct as double)
   + try_cast(Bene_CC_BH_Alcohol_Drug_V1_Pct as double) + try_cast(Bene_CC_BH_Tobacco_V1_Pct as double)
   + try_cast(Bene_CC_BH_Alz_NonAlzdem_V2_Pct as double) + try_cast(Bene_CC_BH_Anxiety_V1_Pct as double)
   + try_cast(Bene_CC_BH_Bipolar_V1_Pct as double) + try_cast(Bene_CC_BH_Mood_V2_Pct as double)
   + try_cast(Bene_CC_BH_Depress_V1_Pct as double) + try_cast(Bene_CC_BH_PD_V1_Pct as double)
   + try_cast(Bene_CC_BH_PTSD_V1_Pct as double) + try_cast(Bene_CC_BH_Schizo_OthPsy_V1_Pct as double)
   + try_cast(Bene_CC_PH_Asthma_V2_Pct as double) + try_cast(Bene_CC_PH_Afib_V2_Pct as double)
   + try_cast(Bene_CC_PH_Cancer6_V2_Pct as double) + try_cast(Bene_CC_PH_CKD_V2_Pct as double)
   + try_cast(Bene_CC_PH_COPD_V2_Pct as double) + try_cast(Bene_CC_PH_Diabetes_V2_Pct as double)
   + try_cast(Bene_CC_PH_HF_NonIHD_V2_Pct as double) + try_cast(Bene_CC_PH_Hyperlipidemia_V2_Pct as double)
   + try_cast(Bene_CC_PH_Hypertension_V2_Pct as double) + try_cast(Bene_CC_PH_IschemicHeart_V2_Pct as double)
   + try_cast(Bene_CC_PH_Osteoporosis_V2_Pct as double) + try_cast(Bene_CC_PH_Parkinson_V2_Pct as double)
   + try_cast(Bene_CC_PH_Arthritis_V2_Pct as double) + try_cast(Bene_CC_PH_Stroke_TIA_V2_Pct as double)
  ) / 100.0                                             as mean_ccw_conditions,
  try_cast(Bene_CC_PH_Diabetes_V2_Pct as double)        as pct_diabetes,
  try_cast(Bene_CC_PH_HF_NonIHD_V2_Pct as double)       as pct_heart_failure,
  try_cast(Bene_CC_BH_Depress_V1_Pct as double)         as pct_depression
from src
