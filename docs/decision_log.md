# Decision log

Implementation decisions and their trade-offs.

| Date | Decision | Reason | Trade-off / revisit when |
|---|---|---|---|
| 2026-10-24 | Use only real public data in findings. | Practice leaders and policy readers need numbers that trace to a file; simulated data would undermine every result. | Patient-level questions (monthly QMB status, same-month conflicts) stay out of scope until a real beneficiary-level source is available. |
| 2026-10-24 | Run the pipeline in GitHub Actions and commit only aggregates. | Source sites are often blocked from development sandboxes; Actions has open network access and a cache for staged Parquet. | Raw files never enter Git; reproducing locally needs network access to the publishers. |
| 2026-10-24 | Define primary care by CMS provider type, with NPs and PAs only when they bill wellness visits. | Without the wellness-visit rule, 316,000 NPs and PAs, most in specialty practice, would swamp the 183,000 primary care physicians. | Some post-acute and nursing-facility NP groups still passed the rule, so a second rule keeps only office-based clinicians (visible office visits, not outnumbered by nursing facility and home visits). |
| 2026-10-24 | Roll clinicians up to practices with the Doctors and Clinicians file. | APCM is billed by practitioners but run by practices; NPI alone is not an organization. | It is a current snapshot applied to 2024, and multi-site systems collapse into one practice. |
| 2026-10-25 | Assign multi-affiliated clinicians to the organization whose members are most often listed nowhere else. | National therapy companies list thousands of primary care physicians who nearly all belong to another group; ranking by size put those physicians in the therapy companies. | A clinician who genuinely splits time between two groups lands in only one; `largest_practices_check.csv` is the check. |
| 2026-10-24 | Treat a missing code row as "fewer than 11 or none" and measure suppression. | CMS hides small cells; treating them as zero would understate small practices. | Readiness for codes with high suppression (TCM, collaborative care) is a lower bound. |
| 2026-10-24 | Estimate QMB patients ecologically (clinician duals times county QMB share). | No public file flags QMBs per clinician, and QMBs drive the highest-paying level. | Off where a practice's duals differ from the county mix. |
| 2026-10-24 | Keep scenario inputs in one seed file and label every dollar figure as a scenario. | The two-condition criterion, capture and consent are not observable in public data. | Replace with observed rates once 2025 APCM claims are published. |
| 2026-10-24 | Train the readiness score on the G2211 launch, with a check model on new care management. | No APCM outcome exists before the 2025 file; G2211 is the closest real primary care code launch. | Probabilities describe G2211, so only the ranking is used; the two models disagree on dual share, which is reported, not hidden. |
| 2026-10-24 | Transcribe APCM rules from the Federal Register and check fees against CMS's payment file. | Vendor guides disagree on rates and eligibility; the final rule and CMS files are authoritative. | Rules need refreshing with each annual fee schedule rule. |
| 2026-10-24 | Serve the app from committed outputs, not live downloads. | Instant start, no dependence on CMS uptime, and the app shows exactly what the pipeline produced. | Data refreshes when the pipeline runs, not on page load. |
| 2026-10-24 | Keep the planner advisory and session-only. | Practices need workflow help, but eligibility, coding and compliance decisions belong to their billing and clinical leads. | No saved progress across sessions; adding it would need storage and privacy review. |
| 2026-10-24 | Disclose AI coding assistance accurately (OpenAI Codex and Anthropic Claude Code). | Accurate authorship matters more than appearances. | The README states which decisions were the analyst's. |

## Decisions to explain in an interview

1. Which conclusions the public files cannot support, and how the design prevents them (suppression, ecological QMB estimates, practice snapshot).
2. Why prior care management billing is a proxy for APCM readiness rather than proof of it.
3. How the G2211 launch works as a training analog, and what would make the forecast wrong.
4. Why the two readiness models disagree on dual share, and what that means for equity.
5. How the fee and rule checks were built, and why vendor sources were not used.
