"""Download real public source files and stage them as Parquet.

Every file is resolved from its publisher at run time, downloaded once, hashed
(SHA-256), filtered to the columns and codes the analysis needs, and written to
data/processed/ (git-ignored). A manifest with URL, retrieval time, byte size,
checksum and output row count is written to pipeline_output/manifests/.

Sources
-------
CMS data.cms.gov
  * Medicare Physician & Other Practitioners: by Provider, by Provider and
    Service, by Geography and Service (service years 2019-2024)
  * Doctors and Clinicians National Downloadable File (current snapshot)
  * Medicare Monthly Enrollment (annual rows; QMB and dual counts by county)
  * Medicare Geographic Variation PUF (traditional Medicare counts, MA rate)
CMS www.cms.gov
  * Physician Fee Schedule relative value files (RVU, GPCI, locality-county)
HRSA data.hrsa.gov
  * Primary care HPSA designations
CDC/ATSDR
  * Social Vulnerability Index 2022, county
Census
  * 2020 ZCTA-to-county relationship file
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get("RAW_DIR", "/tmp/apcm_raw"))
PROC = ROOT / "data" / "processed"
MANI = ROOT / "pipeline_output" / "manifests"
for d in (RAW, PROC, MANI):
    d.mkdir(parents=True, exist_ok=True)

UA = "apcm-opportunity/1.0 (+https://github.com/anandiganguli97/apcm-opportunity)"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]
CODES = json.loads((ROOT / "pipeline" / "hcpcs_codes.json").read_text())
ALL_CODES = sorted({c for fam in CODES.values() for c in fam})


# ----------------------------------------------------------------- helpers
def http_bytes(url: str, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def download(url: str, dest: Path) -> dict:
    """Download with curl (retries, resumable) and return file metadata."""
    if not dest.exists():
        tmp = dest.with_suffix(dest.suffix + ".part")
        for attempt in range(6):
            result = subprocess.run(["curl", "-fsSL", "--retry", "5", "--retry-all-errors", "--retry-delay", "20",
                                     "-A", UA, "-o", str(tmp), url])
            if result.returncode == 0:
                break
            print(f"download failed (curl exit {result.returncode}), attempt {attempt + 1}: {url}", flush=True)
            time.sleep(60 * (attempt + 1))
        else:
            raise RuntimeError(f"Could not download {url}")
        tmp.rename(dest)
    h = hashlib.sha256()
    with dest.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return {"url": url, "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "bytes": dest.stat().st_size, "sha256": h.hexdigest()}


def write_manifest(name: str, entries: list[dict]) -> None:
    (MANI / f"{name}.json").write_text(json.dumps(entries, indent=2) + "\n")


def catalog() -> list[dict]:
    cache = RAW / "data.json"
    if not cache.exists():
        cache.write_bytes(http_bytes("https://data.cms.gov/data.json", timeout=600))
    return json.loads(cache.read_text())["dataset"]


def mup_urls(kind: str) -> dict[int, str]:
    """Map service year -> CSV URL for a Physician & Other Practitioners file."""
    title = f"Medicare Physician & Other Practitioners - {kind}"
    out = {}
    for ds in catalog():
        if ds.get("title", "").split(" : ")[0] != title:
            continue
        for d in ds.get("distribution", []):
            if (d.get("mediaType") or "").endswith("csv") and d.get("downloadURL"):
                temporal = d.get("temporal") or ds.get("temporal")
                if isinstance(temporal, list):
                    temporal = temporal[0].get("startDate", "")
                m = re.search(r"(20\d\d)", str(temporal))
                if m:
                    out[int(m.group(1))] = d["downloadURL"]
    return out


def latest_csv(title_prefix: str) -> str:
    best = None
    for ds in catalog():
        if not ds.get("title", "").startswith(title_prefix):
            continue
        for d in ds.get("distribution", []):
            if (d.get("mediaType") or "").endswith("csv") and d.get("downloadURL"):
                key = ds.get("modified") or ds.get("title")
                if best is None or key > best[0]:
                    best = (key, d["downloadURL"])
    if not best:
        raise RuntimeError(f"No CSV found for {title_prefix}")
    return best[1]


def con() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect()
    c.execute("SET preserve_insertion_order=false; SET memory_limit='10GB'; SET threads=4;")
    return c


def csv_src(path: Path, delim: str = ",") -> str:
    return (f"read_csv('{path}', all_varchar=true, header=true, delim='{delim}', quote='\"', "
            f"ignore_errors=false, max_line_size=4000000)")


def quoted(cols: list[str]) -> str:
    return ", ".join(f'"{c}"' for c in cols)


# ------------------------------------------------------------- MUP files
def ingest_mup(years: list[int], keep_raw: bool) -> None:
    db = con()
    codes_sql = ", ".join(f"'{c}'" for c in ALL_CODES)
    manifest = []
    prov, svc, geo = mup_urls("by Provider"), mup_urls("by Provider and Service"), mup_urls("by Geography and Service")
    for y in years:
        if all((PROC / f"mup_{k}_{y}.parquet").exists() for k in ("prov", "svc", "geo")):
            print(f"MUP {y} already staged", flush=True)
            continue
        # by Provider: clinician profile (all columns except names and street address)
        f = RAW / f"mup_prov_{y}.csv"
        meta = download(prov[y], f)
        cols = [r[0] for r in db.execute(f"DESCRIBE SELECT * FROM {csv_src(f)}").fetchall()]
        drop = {"Rndrng_Prvdr_Last_Org_Name", "Rndrng_Prvdr_First_Name", "Rndrng_Prvdr_MI",
                "Rndrng_Prvdr_St1", "Rndrng_Prvdr_St2"}
        keep = [c for c in cols if c not in drop]
        out = PROC / f"mup_prov_{y}.parquet"
        db.execute(f"COPY (SELECT {y} AS service_year, {quoted(keep)} FROM {csv_src(f)}) TO '{out}' (FORMAT parquet)")
        meta.update(file="by_provider", service_year=y, rows_out=db.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0],
                    columns_out=len(keep) + 1)
        manifest.append(meta)
        if not keep_raw:
            f.unlink()

        # by Provider and Service: only the codes in pipeline/hcpcs_codes.json
        f = RAW / f"mup_svc_{y}.csv"
        meta = download(svc[y], f)
        keep = ["Rndrng_NPI", "Rndrng_Prvdr_Ent_Cd", "Rndrng_Prvdr_State_Abrvtn", "Rndrng_Prvdr_Zip5",
                "Rndrng_Prvdr_RUCA", "Rndrng_Prvdr_Type", "HCPCS_Cd", "Place_Of_Srvc", "Tot_Benes",
                "Tot_Srvcs", "Tot_Bene_Day_Srvcs", "Avg_Mdcr_Alowd_Amt", "Avg_Mdcr_Pymt_Amt"]
        out = PROC / f"mup_svc_{y}.parquet"
        db.execute(f"COPY (SELECT {y} AS service_year, {quoted(keep)} FROM {csv_src(f)} "
                   f"WHERE HCPCS_Cd IN ({codes_sql})) TO '{out}' (FORMAT parquet)")
        total = db.execute(f"SELECT count(*) FROM {csv_src(f)}").fetchone()[0]
        meta.update(file="by_provider_and_service", service_year=y, rows_in=total,
                    rows_out=db.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0], codes=len(ALL_CODES))
        manifest.append(meta)
        if not keep_raw:
            f.unlink()

        # by Geography and Service: national and state totals for the same codes
        f = RAW / f"mup_geo_{y}.csv"
        meta = download(geo[y], f)
        out = PROC / f"mup_geo_{y}.parquet"
        db.execute(f"COPY (SELECT {y} AS service_year, * FROM {csv_src(f)} WHERE HCPCS_Cd IN ({codes_sql})) "
                   f"TO '{out}' (FORMAT parquet)")
        meta.update(file="by_geography_and_service", service_year=y,
                    rows_out=db.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0])
        manifest.append(meta)
        if not keep_raw:
            f.unlink()
        write_manifest("mup", manifest)
        print(f"MUP {y} done", flush=True)


# ------------------------------------------------------- reference files
def ingest_reference() -> None:
    db = con()
    manifest = []

    # Doctors and Clinicians national file: clinician -> group practice
    meta_json = json.loads(http_bytes(
        "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/mj5m-pzi6?show-reference-ids"))
    url = meta_json["distribution"][0]["data"]["downloadURL"]
    f = RAW / "dac.csv"
    meta = download(url, f)
    out = PROC / "dac.parquet"
    db.execute(f"""COPY (SELECT "NPI" AS npi, "Ind_PAC_ID" AS ind_pac_id, org_pac_id, num_org_mem,
                   pri_spec, "Facility Name" AS facility_name, "State" AS state, "ZIP Code" AS zip,
                   grp_assgn FROM {csv_src(f)}) TO '{out}' (FORMAT parquet)""")
    meta.update(file="doctors_and_clinicians", dataset_modified=meta_json.get("modified"),
                rows_out=db.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0])
    manifest.append(meta)
    f.unlink()

    # Medicare Monthly Enrollment: annual rows only
    f = RAW / "monthly_enrollment.csv"
    meta = download(latest_csv("Medicare Monthly Enrollment"), f)
    out = PROC / "monthly_enrollment.parquet"
    db.execute(f"""COPY (SELECT * FROM {csv_src(f)} WHERE MONTH = 'Year'
                   AND TRY_CAST(YEAR AS INTEGER) BETWEEN 2019 AND 2025) TO '{out}' (FORMAT parquet)""")
    meta.update(file="monthly_enrollment", rows_out=db.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0])
    manifest.append(meta)
    f.unlink()

    # Geographic Variation PUF (traditional Medicare), all-ages rows
    f = RAW / "geo_variation.csv"
    meta = download(latest_csv("Medicare Geographic Variation - by National, State & County"), f)
    out = PROC / "geo_variation.parquet"
    db.execute(f"""COPY (SELECT YEAR, BENE_GEO_LVL, BENE_GEO_DESC, BENE_GEO_CD, BENES_TOTAL_CNT,
                   BENES_WTH_PTAPTB_CNT, BENES_OM_CNT, BENES_MA_CNT, MA_PRTCPTN_RATE, BENE_DUAL_PCT
                   FROM {csv_src(f)} WHERE BENE_AGE_LVL = 'All') TO '{out}' (FORMAT parquet)""")
    meta.update(file="geographic_variation", rows_out=db.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0])
    manifest.append(meta)
    f.unlink()

    # The three smaller files below use pandas: HRSA text has stray non-UTF-8 bytes and the
    # SVI and Census files start with a byte-order mark, which trip DuckDB's sniffer.
    import pandas as pd

    # HRSA primary care HPSA
    f = RAW / "hpsa_pc.csv"
    meta = download("https://data.hrsa.gov/DataDownload/DD_Files/BCD_HPSA_FCT_DET_PC.csv", f)
    cols = {"HPSA ID": "hpsa_id", "Designation Type": "designation_type", "HPSA Status": "hpsa_status",
            "HPSA Component Type Description": "component_type",
            "Common State County FIPS Code": "county_fips", "HPSA Score": "hpsa_score", "Rural Status": "rural_status"}
    frame = pd.read_csv(f, dtype=str, encoding="utf-8-sig", encoding_errors="replace", usecols=list(cols)).rename(columns=cols)
    frame.to_parquet(PROC / "hpsa_pc.parquet", index=False)
    meta.update(file="hrsa_hpsa_primary_care", rows_out=len(frame))
    manifest.append(meta)

    # CDC/ATSDR SVI 2022 county
    f = RAW / "svi_2022_county.csv"
    meta = download("https://svi.cdc.gov/Documents/Data/2022/csv/states_counties/SVI_2022_US_county.csv", f)
    frame = pd.read_csv(f, dtype=str, encoding="utf-8-sig", usecols=["FIPS", "ST_ABBR", "COUNTY", "RPL_THEMES"])
    frame.columns = ["county_fips", "state", "county", "svi_overall"]
    frame.to_parquet(PROC / "svi_county.parquet", index=False)
    meta.update(file="svi_2022_county", rows_out=len(frame))
    manifest.append(meta)

    # Census 2020 ZCTA-county relationship; assign each ZCTA to the county with the most land area
    f = RAW / "zcta_county.txt"
    meta = download("https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt", f)
    frame = pd.read_csv(f, sep="|", dtype=str, encoding="utf-8-sig",
                        usecols=["GEOID_ZCTA5_20", "GEOID_COUNTY_20", "AREALAND_PART"])
    frame = frame.dropna(subset=["GEOID_ZCTA5_20"])
    frame["area"] = pd.to_numeric(frame["AREALAND_PART"], errors="coerce").fillna(0)
    frame["land_share"] = frame["area"] / frame.groupby("GEOID_ZCTA5_20")["area"].transform("sum").replace(0, 1)
    frame = frame.sort_values(["GEOID_ZCTA5_20", "area"], ascending=[True, False]).drop_duplicates("GEOID_ZCTA5_20")
    frame = frame.rename(columns={"GEOID_ZCTA5_20": "zcta", "GEOID_COUNTY_20": "county_fips"})[["zcta", "county_fips", "land_share"]]
    frame.to_parquet(PROC / "zcta_county.parquet", index=False)
    meta.update(file="census_zcta_county_2020", rows_out=len(frame))
    manifest.append(meta)

    write_manifest("reference", manifest)
    print("reference done", flush=True)


# ---------------------------------------------------- fee schedule files
def ingest_pfs(release_page: str) -> None:
    """Physician Fee Schedule RVU release: PPRRVU, GPCI and locality-county files."""
    db = con()
    html = http_bytes(release_page).decode("utf-8", "replace")
    zips = sorted(set(re.findall(r'href=["\']([^"\']+\.zip)["\']', html, re.I)))
    if not zips:
        raise RuntimeError(f"No ZIP link on {release_page}")
    url = zips[0] if zips[0].startswith("http") else "https://www.cms.gov" + zips[0]
    f = RAW / "pfs_rvu.zip"
    meta = download(url, f)
    zf = zipfile.ZipFile(f)
    names = zf.namelist()
    meta.update(file="pfs_rvu_release", release_page=release_page, members=names)

    # PPRRVU: header block is 10 lines; columns are positional (see RVU26*.pdf layout)
    rows = []
    for member in names:
        m = re.match(r"PPRRVU(\d{2,4})_(\w+?)_?(nonQPP|QPP)?\.csv$", member, re.I)
        if not m:
            continue
        cf_type = (m.group(3) or "single").lower()
        text = zf.read(member).decode("latin-1").splitlines()
        for rec in __import__("csv").reader(text[10:]):
            if len(rec) < 26 or not rec[0].strip():
                continue
            rows.append({
                "hcpcs": rec[0].strip(), "modifier": rec[1].strip(), "description": rec[2].strip(),
                "status_code": rec[3].strip(), "work_rvu": rec[5], "nonfac_pe_rvu": rec[6],
                "fac_pe_rvu": rec[8], "mp_rvu": rec[10], "nonfac_total_rvu": rec[11],
                "fac_total_rvu": rec[12], "conversion_factor": rec[25], "cf_type": cf_type,
                "source_member": member})
    import pandas as pd  # local import keeps module import light
    pdf = pd.DataFrame(rows)
    pdf.to_parquet(PROC / "pfs_rvu.parquet", index=False)

    # GPCI by locality (header block is 3 lines)
    gp = [n for n in names if re.match(r"GPCI\d{4}\.csv$", n, re.I)]
    grows = []
    for rec in __import__("csv").reader(zf.read(gp[0]).decode("latin-1").splitlines()[3:]):
        if len(rec) >= 8 and rec[0].strip():
            grows.append({"mac": rec[0].strip(), "state": rec[1].strip(), "locality": rec[2].strip(),
                          "locality_name": rec[3].strip(), "pw_gpci_no_floor": rec[4],
                          "pw_gpci_floor": rec[5], "pe_gpci": rec[6], "mp_gpci": rec[7]})
    pd.DataFrame(grows).to_parquet(PROC / "pfs_gpci.parquet", index=False)
    meta.update(rvu_rows=len(pdf), gpci_rows=len(grows))
    write_manifest("pfs", [meta])
    print(f"pfs: {len(pdf)} RVU rows, {len(grows)} GPCI rows from {url}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["mup", "reference", "pfs"])
    ap.add_argument("--years", nargs="*", type=int, default=YEARS)
    ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--pfs-page", default="https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files/rvu26d")
    a = ap.parse_args()
    if a.step == "mup":
        ingest_mup(a.years, a.keep_raw)
    elif a.step == "reference":
        ingest_reference()
    else:
        ingest_pfs(a.pfs_page)
