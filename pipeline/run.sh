#!/usr/bin/env bash
# Entry point for the GitHub Actions pipeline. The job to run is named in
# pipeline/JOB so each step can be re-run on its own.
set -euo pipefail
JOB="$(tr -d '[:space:]' < pipeline/JOB)"
echo "Running job: ${JOB}"
case "${JOB}" in
  probe)
    python pipeline/probe.py
    ;;
  *)
    echo "Unknown job ${JOB}" >&2
    exit 1
    ;;
esac
