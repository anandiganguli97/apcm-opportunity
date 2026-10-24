from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
practices = [
    ("P001", "Northeast Metro Family", "urban", 0, 0.12, 0.18, 0.08, 0.15, 420, 0.10),
    ("P002", "Pine County Health", "rural", 1, 0.31, 0.12, 0.03, 0.08, 185, 0.34),
    ("P003", "Riverbend Primary Care", "suburban", 0, 0.24, 0.23, 0.11, 0.12, 310, 0.24),
    ("P004", "Community Access Clinic", "rural", 1, 0.38, 0.08, 0.01, 0.02, 140, 0.41),
    ("P005", "Lakeside Internal Medicine", "urban", 0, 0.17, 0.30, 0.16, 0.20, 265, 0.13),
]
with (DATA / "practice_profiles.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["practice_id","practice_name","rurality","shortage_area","dual_share","ccm_months_per_100","tcm_months_per_100","bhi_months_per_100","cocm_months_per_100","attributed_beneficiaries","svi_percentile"])
    w.writerows(practices)

months = ["2026-01-01", "2026-02-01", "2026-03-01"]
rows = []
# Deterministic fictional population: illustrative distribution only.
for i in range(1, 61):
    practice = practices[(i * 7 + i // 4) % len(practices)]
    pid = practice[0]
    chronic = (i * 3 + i // 5) % 5
    qmb = int((i * 11) % 100 < practice[4] * 100)
    for m_idx, month in enumerate(months):
        # Vary a small subset over months to make the grain explicit.
        count = max(0, min(7, chronic + (1 if (i + m_idx) % 17 == 0 else 0)))
        rows.append([f"B{i:04d}", month, pid, count, qmb,
                     int((i * 13 + m_idx * 5) % 100 < 30),
                     round(0.0 if (i + m_idx) % 6 else 42.50, 2),
                     "synthetic_plurality_demo"])
with (DATA / "beneficiary_months.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["beneficiary_id","service_month","practice_id","qualifying_chronic_count","qmb_flag","consent_proxy","observed_care_mgmt_allowed_amount","attribution_method"]); w.writerows(rows)
print(f"Wrote {len(rows)} fictional beneficiary-months and {len(practices)} practices")

