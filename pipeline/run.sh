#!/usr/bin/env bash
# Entry point for the GitHub Actions pipeline. The job to run is named in
# pipeline/JOB so each step can be re-run on its own.
set -euo pipefail
JOB="$(tr -d '[:space:]' < pipeline/JOB)"
echo "Running job: ${JOB}"

ingest() {
  # Staged Parquet is cached between runs; only missing pieces are rebuilt.
  [ -f data/processed/mup_prov_2024.parquet ] || python pipeline/ingest.py mup
  [ -f data/processed/svi_county.parquet ] || python pipeline/ingest.py reference
  # Rebuild SVI alone if the cached file fails the numeric-FIPS check
  python -c "import duckdb, sys; sys.exit(0 if duckdb.connect().execute(\"SELECT count(*) FROM 'data/processed/svi_county.parquet' WHERE NOT regexp_full_match(county_fips, '\\d{4,5}')\").fetchone()[0] == 0 else 1)" 2>/dev/null \
    || python pipeline/ingest.py svi
  # Rebuild PFS if either file is missing or the GPCI file has no rows
  python -c "import duckdb, sys; sys.exit(0 if duckdb.connect().execute(\"SELECT count(*) FROM 'data/processed/pfs_gpci.parquet'\").fetchone()[0] > 0 else 1)" 2>/dev/null \
    && [ -f data/processed/pfs_rvu.parquet ] || python pipeline/ingest.py pfs
  python pipeline/profile.py
}

analyze() {
  dbt deps --project-dir . --profiles-dir . || true
  dbt build --project-dir . --profiles-dir .
  python pipeline/export.py
  python pipeline/forecast.py
  python pipeline/build_dashboard.py
}

case "${JOB}" in
  probe)   python pipeline/probe.py ;;
  probe2)  python pipeline/probe2.py ;;
  ingest)  ingest ;;
  analyze) ingest; analyze ;;
  references) python pipeline/references.py $(cat pipeline/REFERENCE_STEPS 2>/dev/null) ;;
  *) echo "Unknown job ${JOB}" >&2; exit 1 ;;
esac
