"""Export aggregate results from the dbt DuckDB database to pipeline_output/results.

Everything written here is aggregate or public-provider-level data from CMS public
use files. Clinician names and street addresses are never exported.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pipeline_output" / "results"
OUT.mkdir(parents=True, exist_ok=True)
db = duckdb.connect(str(ROOT / "apcm_opportunity.duckdb"), read_only=True)


def df(sql: str):
    return db.execute(sql).df()


def save(name: str, sql: str, gz: bool = False) -> None:
    frame = df(sql)
    path = OUT / (f"{name}.csv.gz" if gz else f"{name}.csv")
    frame.to_csv(path, index=False, compression="gzip" if gz else None, float_format="%.6g")
    print(f"{name}: {len(frame)} rows -> {path.name}")


save("national_trend", "select * from mart_national_trend order by service_year")
save("primary_care_exclusions", "select * from mart_primary_care_exclusions order by service_year")
save("suppression_by_code", "select * from mart_suppression order by family, hcpcs, service_year")
save("suppression_by_family", """
    select service_year, family, sum(national_services) national_services, sum(visible_services) visible_services,
           1 - sum(visible_services) / nullif(sum(national_services), 0) invisible_service_share
    from mart_suppression where family is not null group by 1, 2 order by 2, 1""")
save("equity", "select * from mart_equity order by dimension, grp")
save("apcm_opportunity_national", "select * from mart_apcm_opportunity_national order by scenario")
save("fee_schedule_2026", "select hcpcs, family, description, cf_type, nonfac_total_rvu, conversion_factor, national_nonfac_amount, national_fac_amount from stg_pfs_rates order by family, hcpcs, cf_type")
save("readiness_tiers", """
    select readiness_tier, count(*) practices, sum(pcp_clinicians) clinicians, sum(patient_panel_proxy) patient_panel_proxy,
           sum(dual_patients) dual_patients, sum(est_qmb_patients) est_qmb_patients,
           sum(apcm_allowed_base_scenario) apcm_allowed_base_scenario
    from mart_practice group by 1 order by 1""")
save("readiness_by_dual_quintile", """
    with p as (select *, ntile(5) over (order by dual_share) dual_quintile from mart_practice where dual_share is not null)
    select dual_quintile, readiness_tier, count(*) practices, sum(pcp_clinicians) clinicians,
           sum(patient_panel_proxy) patient_panel_proxy, sum(est_qmb_patients) est_qmb_patients,
           min(dual_share) min_dual_share, max(dual_share) max_dual_share
    from p group by 1, 2 order by 1, 2""")
save("state_summary", """
    with c as (
      select state, count(*) clinicians, avg(has_established_care_mgmt::int) share_ccm_or_pcm,
             avg(has_tcm::int) share_tcm, avg(has_awv::int) share_awv,
             sum(dual_cnt)::double / nullif(sum(tot_benes) filter (where dual_cnt is not null), 0) dual_share,
             sum(est_qmb_patients) est_qmb_patients
      from mart_clinician group by 1),
    p as (
      select state, count(*) practices, sum(apcm_allowed_base_scenario) apcm_allowed_base_scenario,
             avg((readiness_tier >= '2')::int) practice_share_ccm_or_pcm
      from mart_practice group by 1)
    select c.*, p.practices, p.apcm_allowed_base_scenario, p.practice_share_ccm_or_pcm
    from c left join p using (state) where c.state is not null order by c.state""")
save("ccm_vs_apcm_summary", """
    select count(*) clinicians_billing_ccm,
           median(ccm_months_per_patient) median_ccm_months_per_patient,
           median(ccm_revenue_per_patient_year) median_ccm_revenue_per_patient_year,
           median(apcm_g0557_same_months) median_apcm_same_months,
           median(apcm_g0557_twelve_months) apcm_twelve_months,
           avg((ccm_minus_apcm_same_months > 0)::int) share_where_apcm_same_months_pays_less,
           avg((ccm_revenue_per_patient_year > apcm_g0557_twelve_months)::int) share_where_apcm_12_months_pays_less
    from mart_ccm_vs_apcm""")
save("ccm_vs_apcm_distribution", """
    select quantile_cont(ccm_months_per_patient, [0.1, 0.25, 0.5, 0.75, 0.9]) months_p10_p90,
           quantile_cont(ccm_revenue_per_patient_year, [0.1, 0.25, 0.5, 0.75, 0.9]) revenue_p10_p90
    from mart_ccm_vs_apcm""")
# Practice-level extract for Tableau (public CMS provider data; no clinician names)
save("practice_extract_tableau", """
    select practice_id, practice_name, state, county_fips, rurality, county_geographic_pc_hpsa, svi_overall,
           pcp_clinicians, pcp_physicians, patient_panel_proxy, dual_patients, round(est_qmb_patients, 1) est_qmb_patients,
           dual_share, avg_hcc_risk_score, readiness_tier, has_ccm, has_pcm, has_tcm, has_bhi_or_cocm, has_rpm,
           has_awv, has_acp, has_g2211, ccm_patient_months, care_mgmt_allowed_visible,
           round(apcm_allowed_full_capture_base, 0) apcm_allowed_full_capture_base,
           round(apcm_allowed_base_scenario, 0) apcm_allowed_base_scenario
    from mart_practice order by patient_panel_proxy desc""", gz=True)

# NPI -> practice lookup for the app's practice search (primary care clinicians, public NPIs, no names)
save("npi_practice_lookup", """
    select npi, practice_id, provider_type, role, state from mart_clinician order by npi""", gz=True)

headline = {
    "analysis_year": int(df("select max(service_year) y from mart_national_trend")["y"][0]),
    "trend": df("select * from mart_national_trend order by service_year").to_dict(orient="records"),
    "equity_all": df("select * from mart_equity where dimension = 'All primary care clinicians'").to_dict(orient="records"),
    "opportunity": df("select * from mart_apcm_opportunity_national order by scenario").to_dict(orient="records"),
    "ccm_vs_apcm": df("select * from mart_ccm_vs_apcm").describe().to_dict(),
}
(OUT / "headline.json").write_text(json.dumps(headline, indent=2, default=str))
print("headline.json written")
