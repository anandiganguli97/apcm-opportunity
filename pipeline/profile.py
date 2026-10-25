"""Profile the staged Parquet files so modelling choices rest on observed values.

Writes pipeline_output/profile/profile.json (aggregate counts only).
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT = ROOT / "pipeline_output" / "profile"
OUT.mkdir(parents=True, exist_ok=True)
db = duckdb.connect()


def q(sql: str) -> list:
    cur = db.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


prof: dict = {}
prov = f"read_parquet('{P}/mup_prov_*.parquet', union_by_name=true)"
svc = f"read_parquet('{P}/mup_svc_*.parquet', union_by_name=true)"
geo = f"read_parquet('{P}/mup_geo_*.parquet', union_by_name=true)"

prof["prov_rows_by_year"] = q(f"SELECT service_year, count(*) n, count(DISTINCT Rndrng_NPI) npis FROM {prov} GROUP BY 1 ORDER BY 1")
prof["prov_types_2024"] = q(f"""SELECT Rndrng_Prvdr_Type AS type, Rndrng_Prvdr_Ent_Cd AS ent, count(*) n,
    sum(TRY_CAST(Tot_Benes AS BIGINT)) benes FROM {prov} WHERE service_year=2024 GROUP BY 1,2 ORDER BY n DESC LIMIT 60""")
prof["prov_dual_missing_2024"] = q(f"""SELECT count(*) n,
    count(*) FILTER (WHERE Bene_Dual_Cnt IS NULL OR Bene_Dual_Cnt='') dual_blank,
    count(*) FILTER (WHERE Bene_Ndual_Cnt IS NULL OR Bene_Ndual_Cnt='') ndual_blank,
    count(*) FILTER (WHERE (Bene_Dual_Cnt IS NULL OR Bene_Dual_Cnt='') AND (Bene_Ndual_Cnt IS NULL OR Bene_Ndual_Cnt='')) both_blank,
    count(*) FILTER (WHERE Bene_Avg_Risk_Scre IS NULL OR Bene_Avg_Risk_Scre='') risk_blank
    FROM {prov} WHERE service_year=2024""")
prof["prov_ruca_values_2024"] = q(f"SELECT Rndrng_Prvdr_RUCA ruca, count(*) n FROM {prov} WHERE service_year=2024 GROUP BY 1 ORDER BY 1")
prof["svc_rows_by_year_code"] = q(f"""SELECT service_year, HCPCS_Cd, count(*) AS n_rows, sum(TRY_CAST(Tot_Srvcs AS DOUBLE)) srvcs,
    sum(TRY_CAST(Tot_Benes AS BIGINT)) benes FROM {svc} GROUP BY 1,2 ORDER BY 2,1""")
prof["svc_place_of_service"] = q(f"SELECT Place_Of_Srvc, count(*) n FROM {svc} GROUP BY 1")
prof["geo_levels"] = q(f"SELECT Rndrng_Prvdr_Geo_Lvl lvl, count(*) n FROM {geo} GROUP BY 1")
prof["geo_national_by_code"] = q(f"""SELECT service_year, HCPCS_Cd, Place_Of_Srvc, Tot_Rndrng_Prvdrs, Tot_Benes, Tot_Srvcs
    FROM {geo} WHERE Rndrng_Prvdr_Geo_Lvl='National' ORDER BY HCPCS_Cd, service_year, Place_Of_Srvc""")

if (P / "dac.parquet").exists():
    d = f"read_parquet('{P}/dac.parquet')"
    prof["dac"] = q(f"""SELECT count(*) AS n_rows, count(DISTINCT npi) npis, count(DISTINCT org_pac_id) orgs,
        count(*) FILTER (WHERE org_pac_id IS NULL OR org_pac_id='') no_org FROM {d}""")
    prof["dac_orgs_per_npi"] = q(f"""SELECT n_orgs, count(*) npis FROM (SELECT npi, count(DISTINCT org_pac_id) n_orgs
        FROM {d} WHERE org_pac_id <> '' GROUP BY 1) GROUP BY 1 ORDER BY 1 LIMIT 15""")
if (P / "monthly_enrollment.parquet").exists():
    m = f"read_parquet('{P}/monthly_enrollment.parquet')"
    prof["enrollment"] = q(f"""SELECT YEAR, BENE_GEO_LVL, count(*) n, sum(TRY_CAST(QMB_ONLY_BENES AS DOUBLE)) qmb_only,
        sum(TRY_CAST(QMB_PLUS_BENES AS DOUBLE)) qmb_plus, sum(TRY_CAST(DUAL_TOT_BENES AS DOUBLE)) dual
        FROM {m} GROUP BY 1,2 ORDER BY 1,2""")
    prof["enrollment_sample_county"] = q(f"SELECT * FROM {m} WHERE BENE_GEO_LVL='County' AND YEAR='2024' LIMIT 3")
if (P / "geo_variation.parquet").exists():
    g = f"read_parquet('{P}/geo_variation.parquet')"
    prof["gv_national"] = q(f"SELECT * FROM {g} WHERE BENE_GEO_LVL='National' ORDER BY YEAR")
if (P / "hpsa_pc.parquet").exists():
    h = f"read_parquet('{P}/hpsa_pc.parquet')"
    prof["hpsa"] = q(f"""SELECT designation_type, hpsa_status, component_type, count(*) n FROM {h}
        GROUP BY 1,2,3 ORDER BY n DESC LIMIT 40""")
if (P / "pfs_rvu.parquet").exists():
    codes = json.loads((ROOT / "pipeline" / "hcpcs_codes.json").read_text())
    allc = ", ".join(f"'{c}'" for fam in codes.values() for c in fam)
    prof["pfs_codes"] = q(f"SELECT * FROM read_parquet('{P}/pfs_rvu.parquet') WHERE hcpcs IN ({allc}) AND modifier='' ORDER BY hcpcs, cf_type")

(OUT / "profile.json").write_text(json.dumps(prof, indent=2, default=str))
print("profile keys:", list(prof))
