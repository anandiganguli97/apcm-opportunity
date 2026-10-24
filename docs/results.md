# What the 2024 public data shows

The dashboard starts with CMS's public Medicare Physician & Other Practitioners by Provider and Service file for 2024. The analysis groups selected prior-care-management billing codes by provider NPI.

| Measure | Result | How to read it |
|---|---:|---|
| Provider NPIs with a visible signal | 45,603 | NPIs with a nonzero service row in at least one of six care-management families. |
| NPIs with signals in at least two families | 8,041 | A simple measure of breadth in visible prior billing experience. |
| NPIs with signals in at least three families | 1,362 | A smaller group with visible experience across several families. |
| Reported service units across selected codes | 14,064,475 | CMS-reported units summed across included codes and places of service; not unique people or APCM months. |

The six families are chronic care management (CCM), complex CCM, principal care management (PCM), transitional care management (TCM), behavioral health integration (BHI), and collaborative care (CoCM). Family totals can overlap because one NPI can appear in more than one family.

## Why it matters

This baseline suggests that prior care-management billing experience is present across many providers, while visible experience across multiple service types is less common. That can help frame workforce and implementation questions: where might training or operational support be useful, and what additional data would be needed to answer that responsibly?

The analysis does **not** show which providers are ready for APCM or which patients would qualify. The CMS file is historical, provider-level, and suppression-limited. Absence of a row is ambiguous. NPI is not a practice identifier, and service units are not patient counts.

The dashboard supports exploration by state, provider type, and CMS RUCA code. RUCA is a rural-urban classification attached to the provider record; it is not a validated practice service area or patient access measure. This version does not claim a rural-urban disparity.

## Reproduce the rollup

```bash
python scripts/download_public_provider_use.py --year 2024
python scripts/build_public_readiness.py --year 2024
```

The resulting one-row-per-NPI file is `data/public_processed/cms_provider_readiness_2024.csv`. The repository includes a snapshot of that derived file so the hosted dashboard can display results immediately; the raw CMS extract is excluded.

