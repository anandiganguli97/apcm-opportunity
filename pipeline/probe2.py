"""Second probe: fee schedule ZIP contents and per-year column names."""
from __future__ import annotations

import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

OUT = Path("pipeline_output/probe")
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "apcm-opportunity-probe/0.2"}
report: dict = {}


def fetch(url: str, nbytes: int | None = None, timeout: int = 300) -> bytes:
    h = dict(UA)
    if nbytes:
        h["Range"] = f"bytes=0-{nbytes - 1}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.read(nbytes) if nbytes else r.read()


# Fee schedule RVU pages -> zip links -> zip contents
pfs = {}
for rel in ["rvu26a", "rvu26b", "rvu26c", "rvu26d", "rvu25a"]:
    page = f"https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files/{rel}"
    try:
        html = fetch(page).decode("utf-8", "replace")
        zips = sorted(set(re.findall(r'href=["\']([^"\']+\.zip)["\']', html, re.I)))
        entry = {"page": page, "zips": zips, "contents": {}}
        for z in zips[:2]:
            url = z if z.startswith("http") else "https://www.cms.gov" + z
            try:
                zf = zipfile.ZipFile(io.BytesIO(fetch(url)))
                entry["contents"][url] = [(i.filename, i.file_size) for i in zf.infolist()]
                for i in zf.infolist():
                    if i.filename.lower().endswith((".csv", ".txt")):
                        head = zf.read(i.filename)[:3000].decode("latin-1", "replace").splitlines()[:12]
                        entry.setdefault("heads", {})[i.filename] = head
            except Exception as exc:  # noqa: BLE001
                entry["contents"][url] = f"ERROR {exc}"
        pfs[rel] = entry
    except Exception as exc:  # noqa: BLE001
        pfs[rel] = f"ERROR {exc}"
report["pfs"] = pfs

# Column names for each year of the provider and geography files
cat = json.loads(Path("pipeline_output/probe/probe_report.json").read_text())["data_cms_gov_datasets"]
cols = {}
for ds in cat:
    t = ds["title"]
    if not t.startswith("Medicare Physician & Other Practitioners"):
        continue
    for d in ds["distributions"]:
        if (d.get("mediaType") or "").endswith("csv"):
            try:
                line = fetch(d["downloadURL"], 20000).decode("utf-8", "replace").splitlines()[0]
                cols[t] = {"url": d["downloadURL"], "columns": line.split(",")}
            except Exception as exc:  # noqa: BLE001
                cols[t] = f"ERROR {exc}"
report["mup_columns"] = cols

(OUT / "probe2_report.json").write_text(json.dumps(report, indent=2))
print("pfs pages:", {k: (len(v["zips"]) if isinstance(v, dict) else v) for k, v in pfs.items()})
print("mup files:", len(cols))
