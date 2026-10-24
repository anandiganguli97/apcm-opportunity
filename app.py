import streamlit as st
import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "apcm_opportunity.duckdb"
st.set_page_config(page_title="APCM Opportunity Explorer", layout="wide")
st.title("APCM Opportunity Explorer")
st.caption("Fictional demonstration only · rates are illustrative placeholders · not a billing recommendation")
if not DB.exists():
    st.error("Build the dbt project first: dbt build --project-dir . --profiles-dir .")
    st.stop()
con = duckdb.connect(str(DB), read_only=True)
practices = con.execute("select practice_id, practice_name from mart_practice_readiness order by practice_name").df()
profiles = con.execute("select * from mart_practice_readiness").df()
left, right = st.columns([2,1])
with left:
    chosen = st.selectbox("Practice", practices.practice_id, format_func=lambda k: practices.loc[practices.practice_id == k, 'practice_name'].iloc[0])
with right:
    scenario = st.select_slider("Scenario", options=["low","base","high"], value="base")
slider1, slider2 = st.columns(2)
with slider1:
    capture = st.slider("Capture rate", 0.0, 1.0, {"low":0.10,"base":0.30,"high":0.60}[scenario], 0.05)
with slider2:
    consent = st.slider("Consent rate", 0.0, 1.0, {"low":0.50,"base":0.75,"high":0.90}[scenario], 0.05)
row = con.execute("select * from mart_practice_opportunity where practice_id=? and scenario=?", [chosen, scenario]).df().iloc[0]
profile = profiles.loc[profiles.practice_id == chosen].iloc[0]
scale = (capture * consent) / max(float(row.capture_rate * row.consent_rate), 0.000001)
projected = float(row.full_capture_gross_allowed) * capture * consent
possible_displaced = float(row.possible_displaced_allowed) * scale
net = projected - possible_displaced
coinsurance = float(row.modeled_coinsurance_exposure) * scale
a,b,c,d = st.columns(4)
a.metric("G0556 patient-months", f"{int(row.g0556_eligible_months):,}")
b.metric("G0557 patient-months", f"{int(row.g0557_eligible_months):,}")
c.metric("G0558 patient-months", f"{int(row.g0558_eligible_months):,}")
d.metric("Billing-signal readiness", f"{profile.billing_readiness_score:.0f}/100")
st.subheader("Modeled opportunity statement")
st.write(f"Projected gross APCM allowed: **${projected:,.0f}** · possible displaced amount: **${possible_displaced:,.0f}** · modeled net: **${net:,.0f}** · estimated coinsurance exposure: **${coinsurance:,.0f}**")
st.caption("Overlap candidates in demo data are exact row-level synthetic inputs. In public aggregate data, same beneficiary-month displacement cannot be identified this way.")
all_rows = con.execute("select * from mart_practice_opportunity where scenario=? order by modeled_net_change desc", [scenario]).df()
st.subheader("Practice comparison")
st.dataframe(all_rows[["practice_name","rurality","g0556_eligible_months","g0557_eligible_months","g0558_eligible_months","projected_apcm_allowed","possible_displaced_allowed","modeled_net_change"]], hide_index=True, use_container_width=True)
st.subheader("Equity proxy")
st.write("Compare G0558 tier volume with observed billing-signal readiness. These fictional profiles demonstrate the analysis only; dual share is an input feature, not a measured national equity result.")
st.scatter_chart(all_rows, x="g0558_eligible_months", y="modeled_net_change", color="rurality")
con.close()
