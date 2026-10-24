"""Download CMS's public NPI x HCPCS service rows for readiness analysis.

This is aggregated provider data, not beneficiary-level claims. Raw files are
written under data/public_raw/ and ignored by git. Example:
  python scripts/download_public_provider_use.py --year 2024
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ID = "92396110-2aed-4d63-a6a2-5d6207d46a29"  # CMS 2024 release, checked 2026-10-24
API_ROOT = "https://data.cms.gov/data-api/v1/dataset"
PAGE_SIZE = 5000
HCPCS_CODES = [
    "99490", "99439", "99487", "99489", "99491", "99437",
    "99424", "99425", "99426", "99427", "99495", "99496",
    "99484", "G0323", "99492", "99493", "99494", "G2214",
    "99091", "99453", "99454", "99457", "99458", "99474",
    "G0511", "G0438", "G0439", "G0402",
]
# Deliberately exclude provider names and street addresses from downloaded output.
KEEP = [
    "Rndrng_NPI", "Rndrng_Prvdr_State_Abrvtn", "Rndrng_Prvdr_Zip5",
    "Rndrng_Prvdr_RUCA", "Rndrng_Prvdr_Type", "Rndrng_Prvdr_Mdcr_Prtcptg_Ind",
    "HCPCS_Cd", "HCPCS_Desc", "Place_Of_Srvc", "Tot_Benes", "Tot_Srvcs",
    "Tot_Bene_Day_Srvcs", "Avg_Mdcr_Alowd_Amt", "Avg_Mdcr_Pymt_Amt",
]


def get_page(dataset_id: str, code: str, offset: int) -> list[dict]:
    query = urllib.parse.urlencode({
        "filter[HCPCS_Cd]": code,
        "size": PAGE_SIZE,
        "offset": offset,
    })
    url = f"{API_ROOT}/{dataset_id}/data?{query}"
    for attempt in range(7):
        req = urllib.request.Request(url, headers={"User-Agent": "apcm-opportunity/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 6:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(60, 2**attempt)
            time.sleep(delay)
        except urllib.error.URLError:
            if attempt == 6:
                raise
            time.sleep(min(60, 2**attempt))
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", default="2024", help="Reporting year label for output")
    parser.add_argument("--dataset-id", default=DEFAULT_DATASET_ID,
                        help="CMS release UUID; verify the current Access API page when refreshing")
    parser.add_argument("--codes", nargs="*", default=HCPCS_CODES,
                        help="Optional HCPCS code subset; defaults to the versioned list in this script")
    args = parser.parse_args()

    outdir = ROOT / "data" / "public_raw"
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / f"cms_provider_service_{args.year}.csv"
    manifest = outdir / f"cms_provider_service_{args.year}_manifest.json"
    partial = outfile.with_suffix(outfile.suffix + ".part")
    partial_manifest = manifest.with_suffix(manifest.suffix + ".part")
    rows_written = 0
    code_counts: dict[str, int] = {}
    with partial.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=KEEP, extrasaction="ignore")
        writer.writeheader()
        for code in args.codes:
            offset = 0
            count = 0
            while True:
                batch = get_page(args.dataset_id, code, offset)
                if not batch:
                    break
                for row in batch:
                    writer.writerow({key: row.get(key, "") for key in KEEP})
                count += len(batch)
                rows_written += len(batch)
                offset += len(batch)
                print(f"{code}: {count} rows", flush=True)
                if len(batch) < PAGE_SIZE:
                    break
                time.sleep(1.0)
            code_counts[code] = count
            time.sleep(1.0)

    partial_manifest.write_text(json.dumps({
        "source": "CMS Medicare Physician & Other Practitioners by Provider and Service",
        "reporting_year": args.year,
        "dataset_uuid": args.dataset_id,
        "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "api_url": f"{API_ROOT}/{args.dataset_id}/data",
        "filter_field": "HCPCS_Cd",
        "codes": code_counts,
        "row_count": rows_written,
        "suppression_note": "Provider-service rows with 10 or fewer beneficiaries are suppressed by CMS.",
        "grain_note": "Provider NPI x HCPCS x place of service; not beneficiary-level and not an APCM claims file.",
    }, indent=2) + "\n", encoding="utf-8")
    os.replace(partial, outfile)
    os.replace(partial_manifest, manifest)
    print(f"Wrote {rows_written} rows to {outfile}")


if __name__ == "__main__":
    main()

