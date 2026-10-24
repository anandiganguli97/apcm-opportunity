# Chronic condition definitions

The CMS by-Provider file reports, for each clinician, the percent of their Medicare patients meeting each of 25 chronic condition flags (`Bene_CC_*_Pct`). CMS's data dictionary defines each as the percent of beneficiaries meeting the Chronic Conditions Data Warehouse (CCW) algorithm for that condition, available for service years 2017 forward. The `_V2` columns use the 30 CCW chronic condition algorithms that a CMS expert panel revised in 2020 (ICD-10 codes only, with modified look-back periods and qualifying claims); the `_V1` columns use the CCW "other chronic or potentially disabling conditions" algorithms.

**How this project uses them.** `stg_mup_provider.mean_ccw_conditions` sums the 25 percentages into a mean condition count per patient, used as a descriptive patient-complexity measure. The flags do not set APCM levels: APCM's "two or more chronic conditions" criterion is a clinical judgment (conditions expected to last 12 months or more that put the patient at significant risk; see `seeds/billing_rules.csv`), so the share of patients meeting it is a scenario input (`seeds/apcm_scenarios.csv`).

**Source.** CCW condition category pages (chronic, and other chronic or disabling), retrieved 2026-10-24 through the Internet Archive because ccwdata.org was down for scheduled maintenance; text and hashes in `pipeline_output/references/ccw_conditions.txt` and `manifest.json`. Columns are matched to CCW conditions by name. Reference period is the look-back window ending in the service year; "HOP" is hospital outpatient, "carrier" is professional claims.

| By-Provider column | CCW condition | CCW set | Reference period | Claims needed to qualify |
|---|---|---|---|---|
| `Bene_CC_PH_Asthma_V2_Pct` | Asthma | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Afib_V2_Pct` | Atrial Fibrillation and Flutter | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Cancer6_V2_Pct` | Cancer, Breast | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Cancer6_V2_Pct` | Cancer, Colorectal | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Cancer6_V2_Pct` | Cancer, Endometrial | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Cancer6_V2_Pct` | Cancer, Lung | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Cancer6_V2_Pct` | Cancer, Prostate | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Cancer6_V2_Pct` | Cancer, Urologic (Kidney, Renal Pelvis, and Ureter) | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_CKD_V2_Pct` | Chronic Kidney Disease | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_COPD_V2_Pct` | Chronic Obstructive Pulmonary Disease | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Diabetes_V2_Pct` | Diabetes | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_HF_NonIHD_V2_Pct` | Heart Failure and Non-Ischemic Heart Disease | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Hyperlipidemia_V2_Pct` | Hyperlipidemia | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Hypertension_V2_Pct` | Hypertension | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_IschemicHeart_V2_Pct` | Ischemic Heart Disease | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Osteoporosis_V2_Pct` | Osteoporosis With or Without Pathological Fracture | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Parkinson_V2_Pct` | Parkinson's Disease and Secondary Parkinsonism | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/Carrier claims with DX codes |
| `Bene_CC_PH_Arthritis_V2_Pct` | Rheumatoid Arthritis/Osteoarthritis | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_PH_Stroke_TIA_V2_Pct` | Stroke/Transient Ischemic Attack | 30 CCW chronic conditions | 1 year | At least 1 inpatient, HOP or carrier claim with DX codes |
| `Bene_CC_BH_Alz_NonAlzdem_V2_Pct` | Alzheimer's Disease | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_BH_Alz_NonAlzdem_V2_Pct` | Non-Alzheimer's Dementia | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_BH_Mood_V2_Pct` | Depression, Bipolar, or Other Depressive Mood Disorders | 30 CCW chronic conditions | 2 years | At least 1 inpatient/SNF/HHA claim OR 2 HOP/carrier claims with DX codes |
| `Bene_CC_BH_ADHD_OthCD_V1_Pct` | ADHD, Conduct Disorders, and Hyperkinetic Syndrome | Other chronic or disabling conditions | 2 years | At least 1 inpatient claim OR 2 other non-drug claims of any service type |
| `Bene_CC_BH_Alcohol_Drug_V1_Pct` | Alcohol Use Disorders | Other chronic or disabling conditions | 2 years | At least 1 inpatient claim OR 2 other non-drug claims of any service type |
| `Bene_CC_BH_Alcohol_Drug_V1_Pct` | Drug Use Disorders | Other chronic or disabling conditions | 2 years | At least 1 inpatient claim OR 2 other non-drug claims of any service type |
| `Bene_CC_BH_Tobacco_V1_Pct` | Tobacco Use Disorders | Other chronic or disabling conditions | 2 years | At least 1 inpatient claim OR 2 other non-drug claims of any service type |
| `Bene_CC_BH_Anxiety_V1_Pct` | Anxiety Disorders | Other chronic or disabling conditions | 2 years | At least 1 inpatient claim OR 2 other non-drug claims of any service type |
| `Bene_CC_BH_Bipolar_V1_Pct` | Bipolar Disorder | Other chronic or disabling conditions | 2 years | At least 1 inpatient claim OR 2 other non-drug claims of any service type |
| `Bene_CC_BH_Depress_V1_Pct` | Depressive Disorders | Other chronic or disabling conditions | 2 years | At least 1 inpatient claim OR 2 other non-drug claims of any service type |
| `Bene_CC_BH_PD_V1_Pct` | Personality Disorders | Other chronic or disabling conditions | 2 years | At least 1 inpatient claim OR 2 other non-drug claims of any service type |
| `Bene_CC_BH_PTSD_V1_Pct` | Post-Traumatic Stress Disorder (PTSD) | Other chronic or disabling conditions | 2 years | At least 1 inpatient claim OR 2 other non-drug claims of any service type |
| `Bene_CC_BH_Schizo_OthPsy_V1_Pct` | Schizophrenia and Other Psychotic Disorders | Other chronic or disabling conditions | 2 years | At least 1 inpatient claim OR 2 other non-drug claims of any service type |
