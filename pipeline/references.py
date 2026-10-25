"""Fetch the reference documents behind the project's rules and checks.

Writes text excerpts and checks under pipeline_output/references/ (public-domain
federal text and CMS files; nothing patient-level):

  fr_<doc>_apcm.txt         APCM passages from the CY2025 and CY2026 PFS final rules,
                            each paragraph tagged with its Federal Register page
  pfs_payment_file.json     CMS National Payment Amount File (PFREV26D) rows for the
                            project's codes, for checking the RVU-based amounts
  mup_docs.txt              CMS by-Provider data dictionary and methodology passages
                            on beneficiary chronic conditions
  ccw_conditions.txt        CCW chronic condition definitions page text
  synthetic_rif.json        What the CMS synthetic claims user guide and catalog list
  manifest.json             URL, retrieval time and SHA-256 of every document fetched
"""
from __future__ import annotations

import html
import io
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest import RAW, catalog, download, http_bytes  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pipeline_output" / "references"
OUT.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)
CODES = ["G0556", "G0557", "G0558", "G0568", "G0569", "G0570", "99490", "99439", "99491", "99487",
         "99424", "99426", "G2211", "99213"]
manifest: list[dict] = []


def fetch(url: str, name: str) -> Path:
    dest = RAW / name
    meta = download(url, dest)
    meta["file"] = name
    manifest.append(meta)
    return dest


def strip_tags(text: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>|</tr>", "\n", text)
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def pdf_text(path: Path) -> str:
    from pypdf import PdfReader
    return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)


# ------------------------------------------------- Federal Register final rules
def federal_register(doc: str, pages: tuple[int, int]) -> None:
    """govinfo's HTML rendition keeps [[Page N]] markers; keep every paragraph on the
    APCM pages plus any paragraph elsewhere that names an APCM code."""
    meta = json.loads(http_bytes(f"https://www.federalregister.gov/api/v1/documents/{doc}.json"))
    date = meta["publication_date"]
    src = fetch(f"https://www.govinfo.gov/content/pkg/FR-{date}/html/{doc}.htm", f"fr_{doc}.htm")
    text = strip_tags(src.read_text(errors="replace"))
    page, out = meta.get("start_page"), []
    key = re.compile(r"APCM|G055[678]|G05(68|69|70)|Advanced Primary Care Management", re.I)
    for para in re.split(r"\n\s*\n", text):
        markers = re.findall(r"\[\[Page (\d+)\]\]", para)
        body = re.sub(r"\s+", " ", re.sub(r"\[\[Page \d+\]\]", " ", para)).strip()
        if body and (pages[0] <= (page or 0) <= pages[1] or key.search(body)):
            out.append(f"[{meta['volume']} FR {page}] {body}")
        if markers:
            page = int(markers[-1])
    header = (f"{meta['title']}\nFederal Register document {doc}, {date}, {meta['volume']} FR "
              f"{meta['start_page']}-{meta['end_page']}\nSource: {src.name} via govinfo.gov\n\n")
    (OUT / f"fr_{doc}_apcm.txt").write_text(header + "\n\n".join(out) + "\n")
    print(f"{doc}: {len(out)} paragraphs kept", flush=True)


# ------------------------------------------------- CMS national payment amounts
def payment_file() -> None:
    """Check the project's fee arithmetic against CMS's own published amounts.

    The National Payment Amount File lists the allowed amount for every code in every
    Medicare locality. Release A (January) is the full file; B, C and D are revisions.
    For each locality and code, the latest release wins; the expected amount is
    (work RVU x PW GPCI + PE RVU x PE GPCI + MP RVU x MP GPCI) x conversion factor
    from the staged RVU26D and GPCI files (non-QP)."""
    import csv
    import pandas as pd
    latest: dict[tuple, dict] = {}
    releases = []
    for rel in "abcd":
        page = f"https://www.cms.gov/medicare/payment/fee-schedules/physician/national-payment-amount-file/pfrev26{rel}"
        body = http_bytes(page).decode("utf-8", "replace")
        for z in sorted(set(re.findall(r'href=["\']([^"\']+\.zip)["\']', body, re.I))):
            url = z if z.startswith("http") else "https://www.cms.gov" + z
            outer = zipfile.ZipFile(fetch(url, Path(url).name))
            for inner in outer.namelist():
                if not inner.lower().endswith("nonqp.zip"):
                    continue
                izf = zipfile.ZipFile(io.BytesIO(outer.read(inner)))
                for member in izf.namelist():
                    if not member.lower().endswith(".txt"):
                        continue
                    rows = list(csv.reader(izf.read(member).decode("latin-1").splitlines()))
                    releases.append({"release": rel, "file": f"{Path(url).name}/{inner}/{member}", "rows": len(rows)})
                    for r in rows:
                        if len(r) >= 7 and r[3] in CODES and not r[4].strip():
                            latest[(r[1], r[2], r[3])] = {"mac": r[1], "locality": r[2], "hcpcs": r[3], "release": rel,
                                                          "cms_nonfac": float(r[5]), "cms_fac": float(r[6])}
    cms = pd.DataFrame(latest.values())
    proc = ROOT / "data" / "processed"
    rvu = pd.read_parquet(proc / "pfs_rvu.parquet")
    rvu = rvu[(rvu.cf_type == "nonqpp") & (rvu.modifier == "") & rvu.hcpcs.isin(CODES)]
    gp = pd.read_parquet(proc / "pfs_gpci.parquet")
    num = lambda x: pd.to_numeric(x, errors="coerce")
    m = cms.merge(gp, on=["mac", "locality"], how="left").merge(rvu, on="hcpcs", how="left")
    pe_nf = num(m.nonfac_pe_rvu); pe_f = num(m.fac_pe_rvu)
    base = num(m.work_rvu) * num(m.pw_gpci_floor) + num(m.mp_rvu) * num(m.mp_gpci)
    m["calc_nonfac"] = ((base + pe_nf * num(m.pe_gpci)) * num(m.conversion_factor)).round(2)
    m["calc_fac"] = ((base + pe_f * num(m.pe_gpci)) * num(m.conversion_factor)).round(2)
    m["diff_nonfac"] = (m.calc_nonfac - m.cms_nonfac).round(2)
    summary = m.groupby("hcpcs").agg(localities=("locality", "size"), unmatched_gpci=("pe_gpci", lambda x: int(x.isna().sum())),
                                     cms_min=("cms_nonfac", "min"), cms_max=("cms_nonfac", "max"),
                                     max_abs_diff=("diff_nonfac", lambda x: float(x.abs().max())),
                                     within_1_cent=("diff_nonfac", lambda x: float((x.abs() <= 0.011).mean()))).reset_index()
    summary.to_csv(OUT / "pfs_payment_check.csv", index=False)
    m[["mac", "locality", "locality_name", "hcpcs", "release", "cms_nonfac", "calc_nonfac", "diff_nonfac", "cms_fac", "calc_fac"]] \
        .sort_values(["hcpcs", "mac", "locality"]).to_csv(OUT / "pfs_payment_check_by_locality.csv", index=False)
    (OUT / "pfs_payment_file.json").write_text(json.dumps({"releases": releases}, indent=1))
    print(summary.to_string(), flush=True)


# ------------------------------------------------- CMS file documentation
def mup_docs() -> None:
    """Data dictionary and methodology of the latest by-Provider release: how CMS
    defines the beneficiary chronic condition columns (Bene_CC_*)."""
    def urls(v):  # catalog fields are a URL string, an object with a URL, or a list of either
        if isinstance(v, str):
            yield v
        elif isinstance(v, dict):
            yield from (x for x in v.values() if isinstance(x, str) and x.startswith("http"))
        elif isinstance(v, list):
            for x in v:
                yield from urls(x)
    sets = [ds for ds in catalog() if ds.get("title", "").startswith("Medicare Physician & Other Practitioners - by Provider :")]
    ds = max(sets, key=lambda d: d.get("temporal", "") if isinstance(d.get("temporal"), str) else json.dumps(d.get("temporal")))
    links = set(urls(ds.get("describedBy"))) | set(urls(ds.get("references")))
    # The dictionary and methodology resource pages render with JavaScript, but the PDF
    # path is embedded in the raw page (often JSON-escaped), so search the raw source.
    for page in sorted({u for u in links if "/resources/" in u} |
                       {"https://data.cms.gov/resources/medicare-physician-other-practitioners-by-provider-data-dictionary",
                        "https://data.cms.gov/resources/medicare-physician-other-practitioners-methodology"}):
        try:
            raw = http_bytes(page).decode("utf-8", "replace").replace("\\/", "/")
            found = set(re.findall(r'(?:https://data\.cms\.gov)?/sites/default/files/[^"\'\s<>]+?\.pdf', raw, re.I))
            links |= {u if u.startswith("http") else "https://data.cms.gov" + u for u in found}
            print(f"{page}: {len(found)} pdf links", flush=True)
        except Exception as e:
            print(f"{page}: {e}", flush=True)
    out = [f"Dataset: {ds.get('title')}"]
    for url in sorted(x for x in links if x.lower().split("?")[0].endswith(".pdf")):
        lines = pdf_text(fetch(url, "mup_" + Path(url).name.replace("%20", "_"))).splitlines()
        keep = set()
        for i, ln in enumerate(lines):
            if re.search(r"Bene_CC|chronic condition|CCW|Chronic Conditions (Data )?Warehouse|look-?back|reference period", ln, re.I):
                keep.update(range(max(0, i - 2), min(len(lines), i + 4)))
        out.append(f"===== {url}\n" + "\n".join(lines[i] for i in sorted(keep)))
    (OUT / "mup_docs.txt").write_text("\n\n".join(out) + "\n")


def ccw_conditions() -> None:
    out = []
    for url in ["https://www2.ccwdata.org/web/guest/condition-categories-chronic",
                "https://www2.ccwdata.org/web/guest/condition-categories-other"]:
        # ccwdata.org goes down for maintenance; fall back to the Internet Archive's latest copy
        for src in (url, "https://web.archive.org/web/2026id_/" + url):
            try:
                path = fetch(src, "ccw_" + ("archive_" if "archive.org" in src else "") + url.rsplit("/", 1)[1] + ".html")
                text = re.sub(r"\n\s*\n+", "\n", strip_tags(path.read_text(errors="replace")))
                if "Down for Maintenance" in text:
                    out.append(f"===== {src}\nUNAVAILABLE: site in maintenance at retrieval")
                    continue
                out.append(f"===== {src}\n{text}")
                break
            except Exception as e:  # keep going; record what failed
                out.append(f"===== {src}\nFAILED: {e}")
    (OUT / "ccw_conditions.txt").write_text("\n\n".join(out) + "\n")


def synthetic_rif() -> None:
    guide = ("https://data.cms.gov/sites/default/files/2023-05/d51e1218-68c3-4c7c-9598-0b81f22fe903/"
             "User%20Guide%20-%20CMS%20Synthetic%20RIF%20Files%20May%202023_AM508_v2.pdf")
    text = pdf_text(fetch(guide, "synthetic_rif_user_guide.pdf"))
    datasets = [{"title": ds.get("title"), "downloads": [d.get("downloadURL") or d.get("accessURL") for d in ds.get("distribution", [])][:20]}
                for ds in catalog() if "synthetic" in (ds.get("title", "") + ds.get("description", "")).lower()]
    (OUT / "synthetic_rif.json").write_text(json.dumps({
        "user_guide": guide, "urls_in_guide": sorted(set(re.findall(r"https?://\S+", text))),
        "file_names_in_guide": sorted(set(re.findall(r"\b[\w-]+\.(?:zip|csv)\b", text, re.I))),
        "guide_excerpt": text[:6000], "catalog_datasets": datasets}, indent=1))


if __name__ == "__main__":
    only = set(sys.argv[1:])  # optional: run only the named steps
    steps = [
        lambda: federal_register("2024-25382", (97859, 97902)),   # CY2025 PFS final rule
        lambda: federal_register("2025-19787", (49464, 49471)),   # CY2026 PFS final rule
        payment_file,
        mup_docs, ccw_conditions, synthetic_rif,
    ]
    failures = 0
    names = ["fr2025", "fr2026", "payment", "mup_docs", "ccw", "synthetic"]
    if only:
        steps = [st for st, n in zip(steps, names) if n in only]
        prev = OUT / "manifest.json"
        if prev.exists():  # keep entries for steps not rerun
            manifest.extend(json.loads(prev.read_text()))
    for step in steps:
        try:
            step()
        except Exception as e:
            failures += 1
            print(f"reference step failed: {type(e).__name__}: {e}", flush=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"references done, {failures} step(s) failed", flush=True)
