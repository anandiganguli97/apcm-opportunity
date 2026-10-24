# Decision log

Entries describe implementation decisions and their trade-offs. They are not claims that an unfinished capability is production-ready.

| Date | Decision | Reason | Trade-off / revisit when |
|---|---|---|---|
| 2026-10-24 | Keep provider aggregates and beneficiary-month tiers on separate analytical paths. | CMS provider-service data has no beneficiary-month join key; combining it would invent patient conflicts and tier mix. | The UI has two surfaces; revisit only when an approved beneficiary-level source is available. |
| 2026-10-24 | Use NPI as provider identity in the public baseline; do not call it a practice organization. | Public claims organize service rows around rendering NPI; group/practice attribution requires a validated crosswalk. | Add organization affiliation only with a dated, sourced NPI-to-TIN/organization linkage and ambiguity audit. |
| 2026-10-24 | Use visible code-family breadth as a simple history signal, not the old 0–100 “readiness score.” | Public provider service files lack attributed-patient denominators and do not observe infrastructure requirements. | Keep breadth interpretable; survey/operational evidence would be needed for true readiness scoring. |
| 2026-10-24 | Treat missing code rows as unknown or unobserved, not zero. | CMS suppression and no billing cannot be distinguished from the public rows alone. | Publish reconciliation only after matched state/national totals and suppression definitions are available. |
| 2026-10-24 | Keep raw and processed CMS extracts out of Git. | Reproducible downloads are preferable to a large brittle checked-in snapshot; local datasets also expand repo exposure. | A small derived public summary may be committed only after licensing, refresh, and size are reviewed. |
| 2026-10-24 | Use a single local DuckDB/dbt workflow and one Streamlit application. | This is enough to demonstrate data lineage and model layering without unsupported cloud/service infrastructure. | Introduce hosted services only for a real multi-user/client use case. |
| 2026-10-24 | Keep the public baseline as the default UI; label the fictional opportunity calculator separately. | A first-time visitor should see real public evidence before a hypothetical scenario; the demo model remains useful for explaining calculations. | Replace fictional sandbox only after validated beneficiary-level public/synthetic pipeline is operational. |
| 2026-10-24 | Disclose OpenAI Codex assistance accurately. | The implementation used Codex; claiming Claude Code or unaided authorship would be false. | Record the model/tool and meaningful human design decisions in the portfolio explanation if the owner chooses to publish them. |

## Current project-owner decisions to explain in an interview

1. Which conclusions are unsupported by the source grain, and why the design prevents them.
2. Why historical care-management use is a proxy signal rather than direct proof of APCM capacity.
3. How code effective dates and suppression change a cross-year/provider comparison.
4. Why local DuckDB/dbt is a better proportionate fit than a cloud stack for this research asset.
5. Which evidence must arrive before a national APCM estimate or adoption forecast can be frozen.

