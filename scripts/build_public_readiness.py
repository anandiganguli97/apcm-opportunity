"""Build a conservative one-row-per-NPI view from the CMS public extract."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apcm_opportunity.public_readiness import build_provider_readiness, write_provider_readiness


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    raw = ROOT / "data" / "public_raw" / f"cms_provider_service_{args.year}.csv"
    catalog = ROOT / "seeds" / "code_families.csv"
    manifest = ROOT / "data" / "public_raw" / f"cms_provider_service_{args.year}_manifest.json"
    if not raw.is_file() or not manifest.is_file():
        raise SystemExit(f"Missing CMS extract or manifest. Run scripts/download_public_provider_use.py --year {args.year} first.")

    rows, summary = build_provider_readiness(raw, catalog, args.year)
    outdir = ROOT / "data" / "public_processed"
    outdir.mkdir(parents=True, exist_ok=True)
    output = outdir / f"cms_provider_readiness_{args.year}.csv"
    write_provider_readiness(rows, output)
    lineage = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_manifest": str(manifest.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": sha256(raw),
        "code_catalog": str(catalog.relative_to(ROOT)).replace("\\", "/"),
        "code_catalog_sha256": sha256(catalog),
        "output": str(output.relative_to(ROOT)).replace("\\", "/"),
        "output_sha256": sha256(output),
        "summary": summary,
    }
    (outdir / f"cms_provider_readiness_{args.year}_lineage.json").write_text(
        json.dumps(lineage, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()

