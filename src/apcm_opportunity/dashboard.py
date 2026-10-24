"""Presentation layer. Analysis rules live in the data and warehouse layers."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


PALETTE = {"ink": "#132D3A", "muted": "#60737D", "teal": "#087E8B", "orange": "#E8884B"}


def _style() -> None:
    st.markdown("""
    <style>
      html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
      .stApp { background: #F4F7F6; color: #132D3A; }
      h1,h2,h3 { font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #132D3A; letter-spacing: -0.035em; }
      .hero { padding: 1.2rem 1.5rem; border-radius: 18px; background: linear-gradient(110deg,#102E3B,#145C65); color:#F3FBFA; margin-bottom:1.1rem; }
      .hero p { color:#C8E5E2; margin:.35rem 0 0 0; }
      .eyebrow { text-transform:uppercase; letter-spacing:.12em; font-size:.72rem; font-weight:700; color:#E7A979; }
      .pill { display:inline-block; border:1px solid #BBDED9; border-radius:99px; padding:.16rem .58rem; color:#087E8B; font-size:.76rem; font-weight:700; margin-right:.35rem; background:#EAF5F3; }
      .note { border-left:4px solid #E8884B; padding:.65rem .9rem; background:#FFF7F0; color:#4D4A43; border-radius:0 9px 9px 0; font-size:.9rem; }
      div[data-testid="stMetric"] { background:#fff; padding: .9rem 1rem; border:1px solid #E4EBE8; border-radius:14px; }
      div[data-testid="stMetricLabel"] { color:#60737D; }
      .block-container { padding-top:2.1rem; padding-bottom:2.5rem; max-width:1440px; }
    </style>
    """, unsafe_allow_html=True)


def _hero(title: str, subtitle: str, tag: str) -> None:
    st.markdown(f'<div class="hero"><div class="eyebrow">{tag}</div><h1 style="color:#fff;margin:.45rem 0 0 0">{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def _public_dashboard(processed: Path, raw_manifest: Path) -> None:
    _hero("Where care-management experience already exists", "A national look at historical Medicare billing signals that could matter as practices consider APCM.", "CMS PUBLIC DATA · 2024 REPORTING YEAR")
    if not processed.exists():
        st.warning("Build the public-data view first. The source downloader and aggregator are included with this project.")
        st.code("python scripts/download_public_provider_use.py --year 2024\npython scripts/build_public_readiness.py --year 2024", language="bash")
        st.stop()

    frame = pd.read_csv(processed, dtype={"provider_npi": str, "zip5": str, "ruca_code": str})
    metadata = {}
    if raw_manifest.exists():
        import json
        metadata = json.loads(raw_manifest.read_text(encoding="utf-8"))
    provider_count = len(frame)
    visible_signal = int(frame["observed_care_management_families"].gt(0).sum())
    multi_family = int(frame["observed_care_management_families"].ge(2).sum())
    ruca_observed = int(frame["ruca_code"].fillna("").astype(str).ne("").sum())
    total_services = int(frame["service_volume_units"].fillna(0).sum())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("NPIs with an observed signal", f"{visible_signal:,}", help="Providers represented in the selected, published predecessor-code rows. This is not all U.S. primary care.")
    m2.metric("Multi-family billing signals", f"{multi_family:,}", help="NPIs with visible rows in at least two predecessor care-management families.")
    m3.metric("Care-management service units", f"{total_services:,}", help="CMS-reported service units summed across selected care-management codes and place of service; not unique patients or months.")
    m4.metric("NPIs with RUCA code", f"{ruca_observed:,}", help="A rural-urban classification code is present. This view does not infer a service area from the NPI address.")
    st.markdown('<div class="note"><b>Interpret carefully.</b> CMS publishes NPI × code × place-of-service aggregates and suppresses low-volume cells. A missing code row can mean no observed billing or a suppressed cell. Historical billing is one readiness clue; it is not an APCM eligibility, capacity, or billing-compliance finding.</div>', unsafe_allow_html=True)

    labels = {
        "ccm_service_units": "CCM", "complex_ccm_service_units": "Complex CCM",
        "pcm_service_units": "PCM", "tcm_service_units": "TCM",
        "bhi_service_units": "Behavioral health", "cocm_service_units": "Collaborative care",
    }
    family = pd.DataFrame({"Family": label, "Service units": int(frame[col].fillna(0).sum()), "NPIs with visible row": int(frame[col].fillna(0).gt(0).sum())} for col, label in labels.items() if col in frame)
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Pre-APCM billing footprint")
        st.bar_chart(family.set_index("Family")[["Service units"]], color=PALETTE["teal"])
    with right:
        st.subheader("Providers by billing breadth")
        breadth = frame["observed_care_management_families"].value_counts().sort_index().rename_axis("Observed families").to_frame("NPI count")
        st.bar_chart(breadth, color=PALETTE["orange"])
        st.caption("Breadth counts distinct predecessor care-management families with an observed nonzero code row.")

    st.subheader("Explore provider signals")
    f1, f2, f3, f4 = st.columns([1, 1, 1, 1.25])
    states = ["All states"] + sorted(frame["state"].dropna().astype(str).unique().tolist())
    types = ["All provider types"] + sorted(frame["provider_type"].dropna().astype(str).unique().tolist())
    ruralities = ["All RUCA codes"] + sorted(frame["ruca_code"].dropna().astype(str).unique().tolist())
    state_filter = f1.selectbox("State", states)
    type_filter = f2.selectbox("Provider type", types)
    ruca_filter = f3.selectbox("RUCA code", ruralities)
    npi_query = f4.text_input("NPI lookup", placeholder="Enter a provider NPI")
    visible = frame.copy()
    if state_filter != "All states": visible = visible[visible["state"].astype(str) == state_filter]
    if type_filter != "All provider types": visible = visible[visible["provider_type"].astype(str) == type_filter]
    if ruca_filter != "All RUCA codes": visible = visible[visible["ruca_code"].astype(str) == ruca_filter]
    if npi_query.strip(): visible = visible[visible["provider_npi"].astype(str).str.contains(npi_query.strip(), regex=False)]
    display_cols = ["provider_npi", "provider_type", "state", "zip5", "ruca_code", "observed_care_management_families", "readiness_breadth_index", "service_volume_units"]
    st.dataframe(visible[display_cols].sort_values("service_volume_units", ascending=False).head(1000), hide_index=True, use_container_width=True, height=420)
    st.caption(f"Showing up to 1,000 of {len(visible):,} matching provider NPIs. Download the visible aggregate table below for local review.")
    st.download_button("Download filtered provider table", visible[display_cols].to_csv(index=False).encode("utf-8"), file_name="apcm_provider_readiness_2024.csv", mime="text/csv")
    st.subheader("Equity question: what this file can and cannot answer")
    st.write("RUCA allows a first-pass rurality comparison of visible historical care-management signals. This public service file does not provide a reliable beneficiary-level QMB × chronic-condition cross-tab for each provider, so it cannot show whether the most G0558-eligible practices are least ready. That requires a different, validated beneficiary-level input and careful handling of suppressed counts.")
    if metadata:
        with st.expander("Source and refresh details"):
            st.write({"source": metadata.get("source"), "reporting year": metadata.get("reporting_year"), "dataset UUID": metadata.get("dataset_uuid"), "API rows downloaded": metadata.get("row_count"), "retrieved UTC": metadata.get("retrieved_utc")})


def _demo_dashboard(root: Path) -> None:
    import duckdb
    db_path = root / "apcm_opportunity.duckdb"
    _hero("APCM opportunity sandbox", "Explore how clinical tier mix, patient consent, capture, and overlapping programs shape a modeled opportunity.", "FICTIONAL INPUTS · ILLUSTRATIVE RATES")
    if not db_path.exists():
        st.info("This teaching sandbox is intentionally separate from public CMS aggregates. Build it with dbt to explore the beneficiary-month model.")
        st.code("dbt build --project-dir . --profiles-dir .")
        st.stop()
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        practices = con.execute("select practice_id, practice_name from mart_practice_readiness order by practice_name").df()
        profiles = con.execute("select * from mart_practice_readiness").df()
        left, right = st.columns([2, 1])
        with left:
            chosen = st.selectbox("Practice", practices.practice_id, format_func=lambda k: practices.loc[practices.practice_id == k, "practice_name"].iloc[0])
        with right:
            scenario = st.select_slider("Scenario", options=["low", "base", "high"], value="base")
        row = con.execute("select * from mart_practice_opportunity where practice_id=? and scenario=?", [chosen, scenario]).df().iloc[0]
        profile = profiles.loc[profiles.practice_id == chosen].iloc[0]
        defaults = {"low": (0.10, 0.50), "base": (0.30, 0.75), "high": (0.60, 0.90)}
        c1, c2 = st.columns(2)
        capture = c1.slider("Capture rate", 0.0, 1.0, defaults[scenario][0], 0.05)
        consent = c2.slider("Consent rate", 0.0, 1.0, defaults[scenario][1], 0.05)
        scale = capture * consent / max(float(row.capture_rate * row.consent_rate), 0.000001)
        projected = float(row.full_capture_gross_allowed) * capture * consent
        displaced = float(row.possible_displaced_allowed) * scale
        net = projected - displaced
        a, b, c, d = st.columns(4)
        a.metric("G0556 beneficiary-months", f"{int(row.g0556_eligible_months):,}")
        b.metric("G0557 beneficiary-months", f"{int(row.g0557_eligible_months):,}")
        c.metric("G0558 beneficiary-months", f"{int(row.g0558_eligible_months):,}")
        d.metric("Billing-signal proxy", f"{profile.billing_readiness_score:.0f}/100")
        st.subheader("Modeled payment statement")
        st.write(f"Gross APCM allowed: **${projected:,.0f}** · possible displaced amount: **${displaced:,.0f}** · modeled net: **${net:,.0f}**")
        st.markdown('<div class="note">Every figure here uses fictional beneficiary-months and illustrative rate placeholders. It demonstrates a calculation, not a forecast, national result, or billing recommendation.</div>', unsafe_allow_html=True)
    finally:
        con.close()


def main(root: Path) -> None:
    st.set_page_config(page_title="APCM Opportunity Lab", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
    _style()
    with st.sidebar:
        st.markdown("### APCM Opportunity Lab")
        st.caption("Medicare · primary care · public evidence")
        surface = st.radio("Analysis surface", ["Public provider baseline", "Opportunity sandbox"], index=0)
        st.markdown("---")
        st.markdown("**Built for transparent decisions**")
        st.caption("Source grain, suppression, and assumptions stay visible beside each result.")
    if surface == "Public provider baseline":
        _public_dashboard(root / "data/public_processed/cms_provider_readiness_2024.csv", root / "data/public_raw/cms_provider_service_2024_manifest.json")
    else:
        _demo_dashboard(root)

