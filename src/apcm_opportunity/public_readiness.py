"""Build a conservative NPI-level readiness signal from CMS public aggregates."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any


READINESS_FAMILIES = ("CCM", "COMPLEX_CCM", "PCM", "TCM", "BHI", "COCM")
FAMILY_LABELS = {
    "CCM": "Chronic care management",
    "COMPLEX_CCM": "Complex CCM",
    "PCM": "Principal care management",
    "TCM": "Transitional care management",
    "BHI": "Behavioral health integration",
    "COCM": "Collaborative care",
}
PROVIDER_FIELDS = {
    "Rndrng_NPI": "provider_npi",
    "Rndrng_Prvdr_State_Abrvtn": "state",
    "Rndrng_Prvdr_Zip5": "zip5",
    "Rndrng_Prvdr_RUCA": "ruca_code",
    "Rndrng_Prvdr_Type": "provider_type",
    "Rndrng_Prvdr_Mdcr_Prtcptg_Ind": "medicare_participating",
}


def _active_code_families(catalog_path: Path, reporting_year: int) -> dict[str, str]:
    as_of = date(reporting_year, 12, 31)
    code_map: dict[str, str] = {}
    with catalog_path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            family = row.get("family", "").strip()
            code = row.get("code", "").strip().upper()
            if family not in READINESS_FAMILIES or not code:
                continue
            start = date.fromisoformat(row["effective_start"])
            end = date.fromisoformat(row["effective_end"]) if row.get("effective_end") else None
            if start <= as_of and (end is None or as_of <= end):
                if code in code_map and code_map[code] != family:
                    raise ValueError(f"Overlapping active family mapping for HCPCS {code}")
                code_map[code] = family
    if not code_map:
        raise ValueError(f"No readiness-code mappings active in {reporting_year}")
    return code_map


def _number(value: str | None, *, field: str, row_number: int) -> float:
    if value is None or value.strip() == "":
        return 0.0
    try:
        number = float(value.replace(",", ""))
    except ValueError as exc:
        raise ValueError(f"Invalid numeric value in {field} at source row {row_number}") from exc
    if number < 0:
        raise ValueError(f"Negative value in {field} at source row {row_number}")
    return number


def build_provider_readiness(raw_path: Path, catalog_path: Path, reporting_year: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Aggregate selected care-management code signals to one row per NPI.

    Missing provider-code rows are never converted into a statement of zero
    capacity. CMS suppression and absence of billing are indistinguishable here.
    """
    code_map = _active_code_families(catalog_path, reporting_year)
    providers: dict[str, dict[str, Any]] = {}
    service_rows = 0
    source_codes: set[str] = set()
    with raw_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"Rndrng_NPI", "HCPCS_Cd", "Tot_Srvcs", "Tot_Benes"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CMS extract is missing required columns: {', '.join(sorted(missing))}")
        for row_number, row in enumerate(reader, start=2):
            code = (row.get("HCPCS_Cd") or "").strip().upper()
            family = code_map.get(code)
            if not family:
                continue
            npi = (row.get("Rndrng_NPI") or "").strip()
            if not npi.isdigit() or len(npi) != 10:
                raise ValueError(f"Invalid provider NPI at source row {row_number}")
            service_rows += 1
            source_codes.add(code)
            if npi not in providers:
                provider: dict[str, Any] = {target: row.get(source, "") for source, target in PROVIDER_FIELDS.items()}
                provider["provider_npi"] = npi
                provider["observed_hcpcs_codes"] = set()
                provider["family_service_units"] = defaultdict(float)
                provider["metadata_conflicts"] = set()
                providers[npi] = provider
            provider = providers[npi]
            for source, target in PROVIDER_FIELDS.items():
                val = (row.get(source) or "").strip()
                if target in provider["metadata_conflicts"]:
                    continue
                prior = provider.get(target, "")
                if val and prior and val != prior:
                    # A provider can have a changed address/RUCA between rows. Do not
                    # silently pick one; blank the conflicting descriptor and record it.
                    provider[target] = ""
                    provider["metadata_conflicts"].add(target)
                elif val and not prior:
                    provider[target] = val
            provider["observed_hcpcs_codes"].add(code)
            provider["family_service_units"][family] += _number(row.get("Tot_Srvcs"), field="Tot_Srvcs", row_number=row_number)

    output: list[dict[str, Any]] = []
    by_family: dict[str, int] = {family: 0 for family in READINESS_FAMILIES}
    for npi in sorted(providers):
        p = providers[npi]
        observed = {family for family, units in p["family_service_units"].items() if units > 0}
        row: dict[str, Any] = {
            **{key: p[key] for key in PROVIDER_FIELDS.values()},
            "reporting_year": reporting_year,
            "observed_code_count": len(p["observed_hcpcs_codes"]),
            "observed_care_management_families": len(observed),
            "readiness_breadth_index": round(100 * len(observed) / len(READINESS_FAMILIES), 1),
            "service_volume_units": round(sum(p["family_service_units"].values()), 2),
            "metadata_conflict_fields": ",".join(sorted(p.get("metadata_conflicts", set()))),
        }
        for family in READINESS_FAMILIES:
            units = round(p["family_service_units"].get(family, 0), 2)
            row[f"{family.lower()}_service_units"] = units
            row[f"has_{family.lower()}_signal"] = family in observed
            by_family[family] += int(family in observed)
        output.append(row)

    summary: dict[str, Any] = {
        "reporting_year": reporting_year,
        "provider_npi_count_with_observed_readiness_codes": len(output),
        "provider_service_rows_in_readiness_scope": service_rows,
        "hcpcs_codes_in_readiness_scope": sorted(source_codes),
        "providers_with_observed_family_signal": by_family,
        "readiness_family_count": len(READINESS_FAMILIES),
        "readiness_index_definition": "100 x count of prior care-management families with an observed nonzero service row / six mapped families",
        "interpretation_limit": "A signal-breadth index from suppressed NPI aggregates; it is not an operational readiness assessment, denominator-adjusted intensity, patient count, APCM eligibility estimate, or billing recommendation.",
    }
    return output, summary


def write_provider_readiness(rows: list[dict[str, Any]], output_path: Path) -> None:
    if not rows:
        raise ValueError("No provider readiness rows to write")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

