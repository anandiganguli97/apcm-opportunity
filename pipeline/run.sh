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
  [ -f data/processed/pfs_rvu.parquet ] || python pipeline/ingest.py pfs
  python pipeline/profile.py
}

analyze() {
  dbt deps --project-dir . --profiles-dir . || true
  dbt build --project-dir . --profiles-dir .
  python pipeline/export.py
}

case "${JOB}" in
  probe)   python pipeline/probe.py ;;
  probe2)  python pipeline/probe2.py ;;
  ingest)  ingest ;;
  analyze) ingest; analyze ;;
  *) echo "Unknown job ${JOB}" >&2; exit 1 ;;
esac
