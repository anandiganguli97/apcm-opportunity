"""Probe public data sources: resolve download URLs and capture schemas.

Runs in GitHub Actions (open internet). Writes pipeline_output/probe/.
Uses only the Python standard library.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

OUT = Path("pipeline_output/probe")
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "apcm-opportunity-probe/0.1 (github.com/anandiganguli97/apcm-opportunity)"}
report: dict = {}


def fetch(url: str, nbytes: int | None = None, timeout: int = 120) -> bytes:
    headers = dict(UA)
    if nbytes:
        headers["Range"] = f"bytes=0-{nbytes - 1}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(nbytes) if nbytes else r.read()


def head_lines(url: str, n: int = 4, nbytes: int = 60000) -> list[str]:
    try:
        raw = fetch(url, nbytes)
        return raw.decode("utf-8", "replace").splitlines()[:n]
    except Exception as exc:  # noqa: BLE001
        return [f"ERROR {type(exc).__name__}: {exc}"]


def links(url: str, pattern: str) -> list[str]:
    try:
        html = fetch(url).decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return [f"ERROR {type(exc).__name__}: {exc}"]
    found = re.findall(r'href=["\']([^"\']+)["\']', html)
    return sorted({f for f in found if re.search(pattern, f, re.I)})


# 1. data.cms.gov catalog
try:
    catalog = json.loads(fetch("https://data.cms.gov/data.json", timeout=300))
    keep = re.compile(
        r"physician & other practitioners|chronic condition|synthetic|dual|"
        r"medicare monthly enrollment|geographic variation|accountable care|shared savings",
        re.I,
    )
    datasets = []
    for ds in catalog.get("dataset", []):
        title = ds.get("title", "")
        if not keep.search(title):
            continue
        dists = []
        for d in ds.get("distribution", []):
            dists.append({k: d.get(k) for k in ("title", "temporal", "downloadURL", "accessURL", "mediaType", "format")})
        datasets.append({"title": title, "identifier": ds.get("identifier"), "temporal": ds.get("temporal"),
                         "landingPage": ds.get("landingPage"), "distributions": dists})
    report["data_cms_gov_datasets"] = datasets
except Exception as exc:  # noqa: BLE001
    report["data_cms_gov_datasets"] = f"ERROR {exc}"

# 2. Headers of the most recent CSV for key datasets
headers = {}
if isinstance(report.get("data_cms_gov_datasets"), list):
    for ds in report["data_cms_gov_datasets"]:
        csvs = [d for d in ds["distributions"] if (d.get("mediaType") or "").endswith("csv") and d.get("downloadURL")]
        csvs.sort(key=lambda d: d.get("temporal") or d.get("title") or "", reverse=True)
        if csvs:
            headers[ds["title"]] = {"url": csvs[0]["downloadURL"], "temporal": csvs[0].get("temporal"),
                                    "lines": head_lines(csvs[0]["downloadURL"])}
report["csv_headers"] = headers

# 3. Doctors and Clinicians national downloadable file (provider-data catalog)
try:
    meta = json.loads(fetch("https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/mj5m-pzi6?show-reference-ids"))
    url = meta["distribution"][0]["data"]["downloadURL"]
    report["dac_national"] = {"url": url, "modified": meta.get("modified"), "lines": head_lines(url)}
except Exception as exc:  # noqa: BLE001
    report["dac_national"] = f"ERROR {exc}"

# 4. Physician fee schedule RVU files
report["pfs_rvu_links"] = links("https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files", r"rvu2[456]|zip")

# 5. HRSA HPSA downloads
report["hrsa"] = {}
for name in ["BCD_HPSA_FCT_DET_PC.csv", "BCD_HPSA_FCT_DET_MH.csv"]:
    url = f"https://data.hrsa.gov/DataDownload/DD_Files/{name}"
    report["hrsa"][name] = {"url": url, "lines": head_lines(url, 3)}

# 6. CDC/ATSDR SVI
report["svi_links"] = links("https://www.atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html", r"csv|svi_?20")
for cand in [
    "https://svi.cdc.gov/Documents/Data/2022/csv/states_counties/SVI_2022_US_county.csv",
    "https://svi.cdc.gov/Documents/Data/2022/csv/states/SVI_2022_US_county.csv",
]:
    report.setdefault("svi_candidates", {})[cand] = head_lines(cand, 2)

# 7. Census ZCTA to county relationship file
z = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt"
report["zcta_county"] = {"url": z, "lines": head_lines(z, 3)}

# 8. CCW chronic condition reference
report["ccw_links"] = links("https://www2.ccwdata.org/web/guest/condition-categories-chronic", r"xlsx|xls|csv|pdf|zip|condition")
report["ccw_links_other"] = links("https://www2.ccwdata.org/web/guest/condition-categories-other", r"xlsx|xls|csv|pdf|zip")

# 9. Synthetic claims collection page
report["synthetic_links"] = links(
    "https://data.cms.gov/collection/synthetic-medicare-enrollment-fee-for-service-claims-and-prescription-drug-event",
    r"zip|csv|download|sites/default/files")

(OUT / "probe_report.json").write_text(json.dumps(report, indent=2))
print(json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in report.items()}, indent=2))
sys.exit(0)
