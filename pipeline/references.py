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
def payment_file(page: str) -> None:
    body = http_bytes(page).decode("utf-8", "replace")
    zips = sorted(set(re.findall(r'href=["\']([^"\']+\.zip)["\']', body, re.I)))
    result = {"page": page, "zips": zips, "files": {}}
    for z in zips:
        url = z if z.startswith("http") else "https://www.cms.gov" + z
        path = fetch(url, Path(url).name)
        zf = zipfile.ZipFile(path)
        for member in zf.namelist():
            if not member.lower().endswith((".csv", ".txt")):
                continue
            lines = zf.read(member).decode("latin-1").splitlines()
            hits = [ln for ln in lines if any(f'"{c}"' in ln or f",{c}," in ln or ln.startswith(c) for c in CODES)]
            result["files"][f"{Path(url).name}/{member}"] = {"rows": len(lines), "head": lines[:12], "code_rows": hits[:4000]}
    (OUT / "pfs_payment_file.json").write_text(json.dumps(result, indent=1))
    print(f"payment file: {len(zips)} zips", flush=True)


# ------------------------------------------------- CMS file documentation
def mup_docs() -> None:
    out = []
    for ds in catalog():
        if not ds.get("title", "").startswith("Medicare Physician & Other Practitioners - by Provider :"):
            continue
        links = {ds.get("describedBy")} | {r for r in ds.get("references", []) if isinstance(r, str)}
        for url in sorted(x for x in links if x and x.lower().endswith(".pdf")):
            path = fetch(url, "mup_" + Path(url).name.replace("%20", "_"))
            text = pdf_text(path)
            keep = [ln for ln in text.splitlines() if re.search(r"chronic|CCW|Bene_CC|condition|lookback|reference period", ln, re.I)]
            out.append(f"===== {url}\n" + "\n".join(keep))
        break  # one release's documentation covers the shared column definitions
    (OUT / "mup_docs.txt").write_text("\n\n".join(out) + "\n")


def ccw_conditions() -> None:
    out = []
    for url in ["https://www2.ccwdata.org/web/guest/condition-categories-chronic",
                "https://www2.ccwdata.org/web/guest/condition-categories-other"]:
        try:
            path = fetch(url, "ccw_" + url.rsplit("/", 1)[1] + ".html")
            text = re.sub(r"\n\s*\n+", "\n", strip_tags(path.read_text(errors="replace")))
            out.append(f"===== {url}\n{text}")
        except Exception as e:  # keep going; record what failed
            out.append(f"===== {url}\nFAILED: {e}")
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
    steps = [
        lambda: federal_register("2024-25382", (97859, 97902)),   # CY2025 PFS final rule
        lambda: federal_register("2025-19787", (49464, 49471)),   # CY2026 PFS final rule
        lambda: payment_file("https://www.cms.gov/medicare/payment/fee-schedules/physician/national-payment-amount-file/pfrev26d"),
        mup_docs, ccw_conditions, synthetic_rif,
    ]
    failures = 0
    for step in steps:
        try:
            step()
        except Exception as e:
            failures += 1
            print(f"reference step failed: {type(e).__name__}: {e}", flush=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"references done, {failures} step(s) failed", flush=True)
