"""Streamlit app: national findings, practice finder, implementation planner and
payment calculator. Reads the committed pipeline outputs, so it starts instantly and
never downloads source data. All analysis lives in the pipeline; this module only
filters, displays and does the user's own what-if arithmetic."""
from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

INK, MUTED, TEAL, BLUE, ORANGE = "#132D3A", "#60737D", "#087E8B", "#2a78d6", "#eb6834"
TIER_COLORS = ["#86b6ef", "#3987e5", "#256abf", "#104281"]
TIER_NAMES = {
    "0 No visible care management": "No visible care management",
    "1 Visit-based services only": "Visit-based services only",
    "2 CCM or PCM": "CCM or PCM only",
    "3 Multi-service care management": "Multi-service care management",
}
SIGNALS = {
    "has_ccm": "Chronic care management", "has_pcm": "Principal care management",
    "has_tcm": "Transitional care management", "has_bhi_or_cocm": "Behavioral health or collaborative care",
    "has_rpm": "Remote monitoring", "has_awv": "Annual wellness visits", "has_acp": "Advance care planning",
    "has_g2211": "Visit complexity add-on (G2211)",
}
FAMILY_NAMES = {"ACP": "Advance care planning", "AWV": "Wellness visits", "BHI": "Behavioral health integration", "CCM": "Chronic care management",
                "COCM": "Collaborative care", "COMPLEXITY_ADDON": "G2211 add-on", "PCM": "Principal care management", "RPM": "Remote monitoring",
                "SDOH_NAVIGATION": "Social needs navigation", "TCM": "Transitional care management", "OFFICE_EM": "Office visits",
                "NURSING_FACILITY": "Nursing facility visits"}
REPO = "https://github.com/anandiganguli97/apcm-opportunity"
ATLAS = "https://anandiganguli97.github.io/apcm-opportunity/"


def _style() -> None:
    st.markdown("""
    <style>
      .stApp { background: #F4F7F6; color: #132D3A; }
      h1, h2, h3 { color: #132D3A; letter-spacing: -0.02em; }
      .band { padding: 1.1rem 1.4rem; border-radius: 12px; background: #102E3B; color: #F3FBFA; margin-bottom: 1rem; }
      .band h1 { color: #fff; margin: .35rem 0 0 0; font-size: 1.9rem; }
      .band p { color: #C8E5E2; margin: .35rem 0 0 0; max-width: 70ch; }
      .eyebrow { text-transform: uppercase; letter-spacing: .1em; font-size: .72rem; font-weight: 700; color: #E7A979; }
      .note { border-left: 4px solid #E8884B; padding: .65rem .9rem; background: #FFF7F0; color: #4D4A43; border-radius: 0 8px 8px 0; font-size: .9rem; }
      .cite { font-size: .8rem; color: #60737D; }
      .chip { display: inline-block; border: 1px solid #BBDED9; border-radius: 99px; padding: .1rem .55rem; margin: 0 .3rem .3rem 0; font-size: .8rem; background: #EAF5F3; color: #087E8B; }
      .chip.off { border-color: #E4EBE8; background: #fff; color: #9AA7AD; text-decoration: line-through; }
      div[data-testid="stMetric"] { background: #fff; padding: .8rem 1rem; border: 1px solid #E4EBE8; border-radius: 12px; }
      .block-container { padding-top: 2rem; padding-bottom: 2.5rem; max-width: 1280px; }
    </style>
    """, unsafe_allow_html=True)


def _band(title: str, subtitle: str, tag: str) -> None:
    st.markdown(f'<div class="band"><div class="eyebrow">{tag}</div><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def _pct(x: float, d: int = 1) -> str:
    return "n/a" if pd.isna(x) else f"{100 * x:.{d}f}%"


def _md(text: str) -> str:
    """Escape dollar signs so Streamlit markdown does not read them as LaTeX."""
    return text.replace("$", "\\$")


def _money(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    if abs(x) >= 1e9:
        return f"${x / 1e9:.1f}B"
    if abs(x) >= 1e6:
        return f"${x / 1e6:.1f}M"
    return f"${x:,.0f}"


# ------------------------------------------------------------------ data
@st.cache_data(show_spinner=False)
def _load(root_path: str) -> dict:
    root = Path(root_path)
    res, fc = root / "pipeline_output" / "results", root / "pipeline_output" / "forecast"
    d = {name: pd.read_csv(res / f"{name}.csv") for name in [
        "national_trend", "equity", "readiness_tiers", "readiness_by_dual_quintile", "state_summary",
        "apcm_opportunity_national", "ccm_vs_apcm_summary", "suppression_by_family", "fee_schedule_2026"]}
    practices = pd.read_csv(res / "practice_extract_tableau.csv.gz", dtype={"practice_id": str, "county_fips": str})
    frozen = fc / "frozen_2025_v1" / "apcm_2025_predictions.csv.gz"  # forecast of record
    scores = pd.read_csv(frozen if frozen.exists() else fc / "draft_2025_apcm_predictions.csv.gz", dtype={"practice_id": str},
                         usecols=["practice_id", "readiness_score", "readiness_decile"])
    d["practices"] = practices.merge(scores, on="practice_id", how="left")
    lookup = res / "npi_practice_lookup.csv.gz"
    d["npi_lookup"] = pd.read_csv(lookup, dtype={"npi": str, "practice_id": str}) if lookup.exists() else pd.DataFrame(columns=["npi", "practice_id"])
    d["rules"] = pd.read_csv(root / "seeds" / "billing_rules.csv").set_index("rule_id")
    loc = pd.read_csv(root / "pipeline_output" / "references" / "pfs_payment_check_by_locality.csv", dtype={"mac": str, "locality": str})
    d["locality_rates"] = loc[loc.hcpcs.isin(["G0556", "G0557", "G0558", "99490"])]
    return d


# ------------------------------------------------------------------ findings
def _findings(d: dict) -> None:
    trend, opp = d["national_trend"], d["apcm_opportunity_national"].set_index("scenario")
    last, first = trend.iloc[-1], trend.iloc[0]
    tq = d["readiness_by_dual_quintile"]
    q5 = tq[tq.dual_quintile == 5]
    q5_none = q5.loc[q5.readiness_tier.str.startswith("0"), "est_qmb_patients"].sum() / q5.est_qmb_patients.sum()
    _band("Who is ready for Medicare's new primary care payment",
          "Advanced Primary Care Management (APCM) pays primary care a monthly fee per patient. Its top tier is for "
          "low-income patients with both Medicare and Medicaid (QMBs). Real CMS data on every traditional Medicare "
          "primary care clinician shows who already runs the care management APCM builds on.",
          f"CMS PUBLIC DATA · {int(first.service_year)} TO {int(last.service_year)}")
    c = st.columns(4)
    c[0].metric("Primary care clinicians", f"{int(last.pcp_clinicians):,}", help="Physicians in family practice, internal medicine, general practice or geriatrics, plus NPs and PAs with visible wellness-visit billing.")
    c[1].metric("Billing CCM or PCM", _pct(last.share_billing_ccm_or_pcm), f"{100 * (last.share_billing_ccm_or_pcm - first.share_billing_ccm_or_pcm):+.1f} pts since {int(first.service_year)}",
                help="Visible chronic or principal care management billing. CMS hides clinician-code rows under 11 patients.")
    c[2].metric("QMBs with no care mgmt*", _pct(q5_none, 0), help="Share of estimated QMB patients whose practice shows no visible care management billing, in the fifth of practices with the highest dual-eligible share.")
    c[3].metric("APCM, base scenario", f"{_money(opp.loc['base', 'allowed_scenario'])} / yr",
                help=f"Traditional Medicare. Range {_money(opp.loc['low', 'allowed_scenario'])} to {_money(opp.loc['high', 'allowed_scenario'])} across scenarios.")

    tabs = st.tabs(["Trend", "Equity", "Where QMB patients are", "Payment", "Opportunity", "Blind spots"])
    with tabs[0]:
        measures = {"share_billing_ccm_or_pcm": "CCM or PCM", "share_billing_tcm": "Transitional care",
                    "share_billing_rpm": "Remote monitoring", "share_billing_acp": "Advance care planning",
                    "share_billing_bhi_or_cocm": "Behavioral health", "share_billing_awv": "Wellness visits"}
        pick = st.multiselect("Services", list(measures.values()), default=["CCM or PCM", "Transitional care", "Remote monitoring"], max_selections=4)
        long = trend.melt(id_vars="service_year", value_vars=list(measures), var_name="m", value_name="share")
        long["Service"] = long.m.map(measures)
        long = long[long.Service.isin(pick)]
        chart = alt.Chart(long).mark_line(point=True, strokeWidth=2).encode(
            x=alt.X("service_year:O", title=None), y=alt.Y("share:Q", title="Share of primary care clinicians", axis=alt.Axis(format="%")),
            color=alt.Color("Service:N", scale=alt.Scale(range=[BLUE, ORANGE, "#1baf7a", "#6250d6"]), legend=alt.Legend(orient="top", title=None)),
            tooltip=["service_year", "Service", alt.Tooltip("share:Q", format=".1%")])
        st.altair_chart(chart.properties(height=320), width="stretch")
        st.caption("Source: pipeline_output/results/national_trend.csv")
    with tabs[1]:
        eq = d["equity"]
        dims = {"Dual-eligible share of panel (quintile)": "Dual share of panel", "Rurality (clinician ZIP, RUCA)": "Rurality",
                "County primary care shortage area": "Shortage area", "Social Vulnerability Index (county quartile)": "Social vulnerability"}
        dim = st.radio("Compare by", list(dims), format_func=dims.get, horizontal=True)
        rows = eq[(eq.dimension == dim) & (eq.grp != "Unknown")]
        long = rows.melt(id_vars=["grp", "clinicians"], value_vars=["dual_patient_share_with_ccm_or_pcm", "nondual_patient_share_with_ccm_or_pcm"], var_name="who", value_name="share")
        long["Patients"] = long.who.map({"dual_patient_share_with_ccm_or_pcm": "Dual-eligible", "nondual_patient_share_with_ccm_or_pcm": "Other Medicare"})
        chart = alt.Chart(long).mark_bar(cornerRadiusEnd=3).encode(
            y=alt.Y("grp:N", title=None, sort=list(rows.grp)), yOffset="Patients:N",
            x=alt.X("share:Q", title="Share of patients whose clinician bills CCM or PCM", axis=alt.Axis(format="%")),
            color=alt.Color("Patients:N", scale=alt.Scale(range=[BLUE, ORANGE]), legend=alt.Legend(orient="top", title=None)),
            tooltip=["grp", "Patients", alt.Tooltip("share:Q", format=".1%"), alt.Tooltip("clinicians:Q", format=",")])
        st.altair_chart(chart.properties(height=60 * len(rows)), width="stretch")
        st.caption("Clinicians with a reported dual-eligible count (CMS blanks it for small panels). Source: pipeline_output/results/equity.csv")
    with tabs[2]:
        tq = tq.assign(Tier=tq.readiness_tier.map(TIER_NAMES))
        tq["share"] = tq.est_qmb_patients / tq.groupby("dual_quintile").est_qmb_patients.transform("sum")
        tq["Fifth"] = "Fifth " + tq.dual_quintile.astype(str) + tq.dual_quintile.map({1: " (fewest duals)", 5: " (most duals)"}).fillna("")
        chart = alt.Chart(tq).mark_bar().encode(
            y=alt.Y("Fifth:N", title="Practices by dual-eligible share", sort=None),
            x=alt.X("share:Q", stack="normalize", title="Share of estimated QMB patients", axis=alt.Axis(format="%")),
            color=alt.Color("Tier:N", sort=list(TIER_NAMES.values()), scale=alt.Scale(domain=list(TIER_NAMES.values()), range=TIER_COLORS), legend=alt.Legend(orient="top", title=None, columns=2)),
            order=alt.Order("readiness_tier:N"),
            tooltip=["Fifth", "Tier", alt.Tooltip("share:Q", format=".0%"), alt.Tooltip("est_qmb_patients:Q", format=",.0f")])
        st.altair_chart(chart.properties(height=300), width="stretch")
        st.caption("QMB patients are estimated from each clinician's dual-eligible count and the county QMB share. Source: pipeline_output/results/readiness_by_dual_quintile.csv")
    with tabs[3]:
        cv = d["ccm_vs_apcm_summary"].iloc[0]
        fee = d["fee_schedule_2026"].query("cf_type == 'nonqpp'").set_index("hcpcs").national_nonfac_amount
        bars = pd.DataFrame({"Billing pattern": ["CCM as billed (median clinician)", "G0557 in the same months", "G0557 every month", "G0558 every month (QMB)"],
                             "Per patient per year": [cv.median_ccm_revenue_per_patient_year, cv.median_apcm_same_months, cv.apcm_twelve_months, 12 * fee["G0558"]]})
        chart = alt.Chart(bars).mark_bar(cornerRadiusEnd=3, color=BLUE).encode(
            y=alt.Y("Billing pattern:N", sort=None, title=None), x=alt.X("Per patient per year:Q", axis=alt.Axis(format="$,.0f")),
            tooltip=["Billing pattern", alt.Tooltip("Per patient per year:Q", format="$,.0f")])
        st.altair_chart(chart.properties(height=200), width="stretch")
        st.write(_md(f"G0557 pays {_money(fee['G0557'])}/month against {_money(fee['99490'])} for base CCM, with no minimum minutes. "
                 f"The median CCM biller billed {cv.median_ccm_months_per_patient:.1f} months per patient in 2024. Billing G0557 every month would pay "
                 f"{_pct(1 - cv.share_where_apcm_12_months_pays_less, 0)} of CCM billers more per patient."))
        st.caption("CY2026 national non-facility rates. Sources: pipeline_output/results/ccm_vs_apcm_summary.csv, fee_schedule_2026.csv")
    with tabs[4]:
        t = opp.reset_index()[["scenario", "share_2plus_qmb", "share_2plus_non_qmb", "capture_rate", "consent_rate", "allowed_scenario", "patient_coinsurance_scenario"]]
        t.columns = ["Scenario", "2+ conditions (QMB)", "2+ conditions (others)", "Capture", "Consent", "Allowed per year", "Patient coinsurance"]
        st.dataframe(t.style.format({c: "{:.0%}" for c in t.columns[1:5]} | {"Allowed per year": _money, "Patient coinsurance": _money}), hide_index=True, width="stretch")
        st.write(_md(f"Full enrollment of every eligible traditional Medicare patient would be {_money(opp.loc['low', 'allowed_full_capture'])} to {_money(opp.loc['high', 'allowed_full_capture'])} a year. "
                 "The scenario inputs are assumptions; no public file measures APCM's clinical criterion or consent."))
    with tabs[5]:
        sup = d["suppression_by_family"]
        sup = sup[(sup.service_year == sup.service_year.max()) & sup.family.notna()].sort_values("invisible_service_share", ascending=False)
        sup = sup.assign(family=sup.family.map(FAMILY_NAMES).fillna(sup.family))
        chart = alt.Chart(sup).mark_bar(cornerRadiusEnd=3, color=BLUE).encode(
            y=alt.Y("family:N", sort=None, title=None), x=alt.X("invisible_service_share:Q", title="Share of national services hidden at clinician level", axis=alt.Axis(format="%")),
            tooltip=["family", alt.Tooltip("invisible_service_share:Q", format=".1%")])
        st.altair_chart(chart.properties(height=320), width="stretch")
        st.caption("CMS drops clinician-code rows with fewer than 11 patients. CCM is well measured; TCM is not.")
    st.markdown(f"Full report: [APCM Readiness Atlas]({ATLAS}) · Methods and checks: [GitHub]({REPO})")


# ------------------------------------------------------------------ practice finder
def _profile(p: pd.Series) -> None:
    st.markdown(f"### {p.practice_name if isinstance(p.practice_name, str) else 'Solo clinician ' + p.practice_id.removeprefix('npi:')}")
    st.caption(f"{p.state} · {p.rurality} · {'primary care shortage county' if str(p.county_geographic_pc_hpsa) == 'True' else 'not a shortage county'} · practice ID {p.practice_id}")
    c = st.columns(4)
    c[0].metric("Primary care clinicians", f"{int(p.pcp_clinicians):,}")
    c[1].metric("Medicare patients (sum across clinicians)", f"{int(p.patient_panel_proxy):,}")
    c[2].metric("Dual-eligible share", _pct(p.dual_share), f"~{p.est_qmb_patients:,.0f} QMB patients" if pd.notna(p.est_qmb_patients) else None, delta_color="off")
    c[3].metric("Readiness score", "n/a" if pd.isna(p.readiness_score) else f"{p.readiness_score:.0f} / 100",
                help="Percentile of predicted likelihood of early APCM billing, from a model trained on how practices took up G2211 in 2024. Frozen on 25 Oct 2026, before CMS published 2025 data.")
    chips = "".join(f'<span class="chip{"" if str(p[k]) == "True" else " off"}">{v}</span>' for k, v in SIGNALS.items())
    st.markdown(f"**Visible 2024 billing** ({TIER_NAMES.get(p.readiness_tier, p.readiness_tier)})<br>{chips}", unsafe_allow_html=True)
    st.markdown(f'<div class="cite">A struck-through service means no visible row, which can mean fewer than 11 patients rather than none. '
                f'Base-scenario APCM allowed amount for this practice: {_money(p.apcm_allowed_base_scenario).replace("$", "&#36;")} a year (assumptions on the Findings page). '
                'Patient counts add up across clinicians and can count shared patients twice.</div>', unsafe_allow_html=True)


def _finder(d: dict) -> None:
    _band("Find a practice", "Search 51,000+ primary care practices: group practices from CMS's Doctors and Clinicians file, plus solo clinicians. "
          "See what each already bills, its patient mix and its readiness score.", "PRACTICE FINDER · 2024")
    pr = d["practices"]
    f = st.columns([1.3, 1, 1, 1.2])
    query = f[0].text_input("Practice name or clinician NPI", placeholder="e.g. 1234567890 or 'family medicine'")
    state = f[1].selectbox("State", ["All"] + sorted(pr.state.dropna().unique()))
    tier = f[2].selectbox("Readiness tier", ["All"] + list(TIER_NAMES.values()))
    min_clin = f[3].slider("Minimum clinicians", 1, 50, 1)
    g = st.columns([1, 1, 2])
    rural = g[0].selectbox("Rurality", ["All", "Metropolitan", "Micropolitan", "Small town", "Rural"])
    hpsa = g[1].selectbox("Shortage area", ["All", "Shortage county", "Not a shortage county"])
    sort = g[2].radio("Sort by", ["Estimated QMB patients", "Readiness score (low first)", "Readiness score (high first)", "Patients"], horizontal=True)

    v = pr
    if query.strip():
        q = query.strip()
        if q.isdigit() and len(q) == 10:
            ids = d["npi_lookup"].loc[d["npi_lookup"].npi == q, "practice_id"]
            v = v[v.practice_id.isin(ids) | (v.practice_id == f"npi:{q}")]
            if v.empty:
                st.info("That NPI is not a primary care clinician in the 2024 file (or has fewer than 11 Medicare patients).")
        else:
            v = v[v.practice_name.fillna("").str.contains(q, case=False, regex=False)]
    if state != "All": v = v[v.state == state]
    if tier != "All": v = v[v.readiness_tier.map(TIER_NAMES) == tier]
    if rural != "All": v = v[v.rurality == rural]
    if hpsa != "All": v = v[v.county_geographic_pc_hpsa.astype(str) == ("True" if hpsa == "Shortage county" else "False")]
    v = v[v.pcp_clinicians >= min_clin]
    key, asc = {"Estimated QMB patients": ("est_qmb_patients", False), "Readiness score (low first)": ("readiness_score", True),
                "Readiness score (high first)": ("readiness_score", False), "Patients": ("patient_panel_proxy", False)}[sort]
    v = v.sort_values(key, ascending=asc, na_position="last")
    st.caption(f"{len(v):,} practices match. Showing the first 500.")
    show = v.head(500).assign(Tier=lambda x: x.readiness_tier.map(TIER_NAMES))[
        ["practice_name", "state", "rurality", "pcp_clinicians", "patient_panel_proxy", "dual_share", "est_qmb_patients", "Tier", "readiness_score", "practice_id"]]
    show.columns = ["Practice", "State", "Rurality", "Clinicians", "Patients", "Dual share", "Est. QMB", "Tier", "Readiness score", "Practice ID"]
    event = st.dataframe(show, hide_index=True, width="stretch", height=380, on_select="rerun", selection_mode="single-row",
                         column_config={"Dual share": st.column_config.NumberColumn(format="%.2f"), "Est. QMB": st.column_config.NumberColumn(format="%.0f"),
                                        "Readiness score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f")})
    st.download_button("Download these practices (CSV)", v.to_csv(index=False).encode("utf-8"), "apcm_practices.csv", "text/csv")
    picked = event.selection.rows if event and hasattr(event, "selection") else []
    if picked:
        p = v.iloc[picked[0]]
        st.markdown("---")
        _profile(p)
        b = st.columns(2)
        if b[0].button("Plan APCM for this practice", type="primary"):
            st.session_state["practice_id"] = p.practice_id
            st.session_state["nav_target"] = "Plan APCM next steps"
            st.rerun()
        if b[1].button("Estimate APCM payment for this practice"):
            st.session_state["practice_id"] = p.practice_id
            st.session_state["nav_target"] = "Payment calculator"
            st.rerun()
    else:
        st.info("Select a row to see the practice profile and plan from it.")
    st.markdown('<div class="note">Practice membership comes from CMS\'s current Doctors and Clinicians file. Some large "practices" are post-acute or '
                'nursing-facility groups whose nurse practitioners bill wellness visits; treat them with care.</div>', unsafe_allow_html=True)


READINESS_QUESTIONS = [
    {
        "area": "Accountable primary-care lead",
        "question": "Is a qualified clinician identified to direct the team and serve as the continuing focal point for the patient’s primary care?",
        "owner": "Clinical lead and practice manager",
        "purpose": "Make responsibility clear to patients, staff, and other providers, including when the usual clinician is unavailable.",
        "steps": [
            "Name the clinician who is accountable for primary care coordination and identify a qualified backup for absences.",
            "Write down which team members handle outreach, clinical review, scheduling, records, and billing questions. Confirm supervision and state-scope requirements with the practice’s compliance lead.",
            "Set a short weekly implementation huddle. Use it to review unresolved workflow issues, patient access problems, and handoffs between clinical and administrative staff.",
            "Tell front-desk, clinical, and billing staff who owns each question and how to route something they cannot resolve.",
        ],
        "deliverable": "A one-page responsibility map with a named clinical lead, backup, team roles, and escalation route.",
        "done_when": "Staff can name the accountable clinician and correctly route a sample urgent call, care-plan question, and billing question.",
        "priority": "Start here",
    },
    {
        "area": "Patient consent and enrollment",
        "question": "Can the practice explain the service and document patient consent before APCM services start?",
        "owner": "Clinical operations lead and billing/compliance lead",
        "purpose": "Ensure the patient understands what is being offered and that the record supports the practice’s enrollment workflow.",
        "steps": [
            "Draft a plain-language conversation guide and written or verbal consent workflow. Have the practice’s compliance or billing lead review it against current CMS and payer guidance.",
            "Make sure the explanation covers the one-provider-per-calendar-month rule, the patient’s right to stop at any time, and that cost sharing may apply.",
            "Choose the exact place in the health record to record the consent date, whether it was written or verbal, who obtained it, and any required supporting details.",
            "Add an enrollment stop: staff should not mark APCM as active until consent is documented before services begin.",
            "Train staff with a short role-play, including how to answer questions without promising savings or coverage.",
            "For a small sample of enrollments, have a second staff member confirm the consent record is complete and easy to find.",
        ],
        "deliverable": "An approved patient explanation, documentation field or template, and enrollment checklist.",
        "done_when": "A staff member can demonstrate the conversation and another can locate the consent record in a test chart.",
        "priority": "Before pilot enrollment",
    },
    {
        "area": "Patient eligibility and initiating-visit check",
        "question": "Does the team verify current APCM eligibility and whether an initiating visit is needed before enrollment?",
        "owner": "Billing lead with the clinical lead",
        "purpose": "Prevent enrollment and claim workflows from relying on memory or assumptions about a patient’s prior care.",
        "steps": [
            "Ask the billing lead to turn current CMS and Medicare Administrative Contractor guidance into a short, dated eligibility reference. Do not use this planner to decide eligibility or select a billing code.",
            "Create a record checklist for the relevant coverage and patient criteria, the responsible billing practitioner, and the initiating-visit review.",
            "For the initiating-visit review, capture the relevant prior visit or care-management history and route exceptions to the billing lead. CMS describes exceptions, including certain recent visits and prior care-management services; staff should verify the exact current rule before use.",
            "Configure the enrollment workflow so an unresolved eligibility or initiating-visit question goes to a qualified reviewer before activation.",
            "Test the checklist using fictional or de-identified training cases. Check that staff can distinguish a confirmed case from one needing review.",
        ],
        "deliverable": "A dated eligibility reference, chart checklist, and escalation path for uncertain cases.",
        "done_when": "A reviewer can explain where the current rule came from and demonstrate how an uncertain case is held for review.",
        "priority": "Before pilot enrollment",
    },
    {
        "area": "24/7 access and continuity",
        "question": "Can patients with urgent needs reach the care team at any time, and can the team access current records and support ongoing appointments?",
        "owner": "Practice manager and clinical operations lead",
        "purpose": "Make urgent access reliable after hours while preserving continuity with a designated care-team member.",
        "steps": [
            "Map the patient’s route for urgent needs during business hours, evenings, weekends, and holidays. Identify who answers, who triages, and when the patient is directed to emergency services.",
            "Check that the route reaches a person or monitored service with a clear handoff to the clinical team; post the same instructions in the patient-facing materials.",
            "Confirm authorized clinicians can retrieve the information they need when covering after hours, including the current care plan and medication information.",
            "Define how patients can schedule follow-up with a designated team member and how the team handles a request when that person is unavailable.",
            "Run a documented test call outside normal business hours. Record the route, response, any failure, owner, and retest date.",
        ],
        "deliverable": "A coverage and escalation map, patient instructions, and a dated after-hours test record.",
        "done_when": "A test call reaches the correct clinical route and the covering staff member can access the relevant record.",
        "priority": "Before pilot enrollment",
    },
    {
        "area": "Needs assessment and ongoing care management",
        "question": "Does the team have a repeatable way to understand medical and psychosocial needs, preventive-care needs, and medication concerns?",
        "owner": "Nurse or care-management lead, with clinical oversight",
        "purpose": "Turn patient needs into assigned follow-up rather than a one-time assessment that sits in the chart.",
        "steps": [
            "Select an assessment process already supported by the practice. Include medical and psychosocial needs, functional concerns, patient strengths, support needs, and preventive-care needs.",
            "Decide when the assessment is completed, who reviews it, and what changes require a clinician’s attention. Confirm the workflow fits staff qualifications and supervision rules.",
            "Set a medication-reconciliation process: identify the current medication list, compare it with available sources, and route discrepancies or safety concerns to the appropriate clinician.",
            "For each identified need, create an action with an owner, due date, and follow-up status. Close the loop when the patient or referring provider has been contacted.",
            "Review a small, de-identified workflow sample in a staff huddle to find missing handoffs and simplify the process before expanding.",
        ],
        "deliverable": "A repeatable needs-assessment workflow and a work queue for follow-up actions.",
        "done_when": "A sample assessment leads to a documented owner, next action, and appropriate clinical review.",
        "priority": "Before pilot enrollment",
    },
    {
        "area": "Patient-centered electronic care plan",
        "question": "Can the team create, update, share, and provide the patient or caregiver a copy of a comprehensive care plan?",
        "owner": "Clinical lead and health-record administrator",
        "purpose": "Keep the patient’s goals and the team’s responsibilities visible and usable across care settings.",
        "steps": [
            "Review the health record’s existing care-plan tools before building a new template. Ask clinicians what they need to see during a handoff.",
            "Agree on a simple structure for the patient’s goals and preferences, relevant needs and supports, responsible team members, planned actions, and follow-up dates.",
            "Define who can create, update, and view the plan. Make sure appropriate team members can find it without searching across multiple chart locations.",
            "Write a process for sharing the plan with relevant outside providers when appropriate and giving a copy to the patient or caregiver.",
            "Test the template with a fictional case. Ask a second team member to find the goals, next steps, and plan owner; revise anything that is hard to locate.",
        ],
        "deliverable": "A tested electronic care-plan template, access rules, and a process for sharing a patient copy.",
        "done_when": "A second team member can find the current plan and identify its owner and next follow-up without coaching.",
        "priority": "Before pilot enrollment",
    },
    {
        "area": "Transitions, referrals, and follow-up",
        "question": "Can the practice detect important care transitions, track referrals, exchange records, and follow up when clinically indicated?",
        "owner": "Care-coordination lead and referral coordinator",
        "purpose": "Reduce the chance that a discharge or referral disappears between organizations.",
        "steps": [
            "List the transition signals the practice can reliably receive today, such as discharge notifications, patient calls, or referral results. Identify the gaps and a backup way to learn about events.",
            "Create one shared queue with the event date, source, assigned staff member, next action, due date, and closure status. Avoid keeping the operational queue in personal spreadsheets without approved safeguards.",
            "Set a daily review and escalation route for high-priority events. Define how clinical staff decide which follow-up is clinically indicated.",
            "For discharge events, build a process for timely exchange of electronic health information and timely follow-up communication. CMS specifies follow-up within 7 days when clinically indicated; have the clinical lead define how that decision is documented.",
            "Track referrals from order through appointment or documented reason they could not be completed. Return relevant updates to the responsible clinician.",
            "Test the process with a fictional discharge and referral. Measure how long each handoff takes and fix the first point where ownership becomes unclear.",
        ],
        "deliverable": "A transition/referral queue, owner and escalation rules, and a documented test.",
        "done_when": "A test discharge and referral each have an owner, due date, clinical review path, and clear closure status.",
        "priority": "Before pilot enrollment",
    },
    {
        "area": "Secure communication options",
        "question": "Can patients use secure non-phone communication, and does the practice have a safe process to review and route those messages?",
        "owner": "Clinical operations lead and privacy/security lead",
        "purpose": "Offer practical communication options without leaving messages unread or sending clinical details through an unapproved channel.",
        "steps": [
            "Inventory the secure patient-facing tools already approved by the organization, such as its patient portal or secure messaging system.",
            "Choose which types of requests each channel accepts and publish clear instructions for urgent needs, expected response times, and after-hours routing.",
            "Assign who checks each inbox, how often it is reviewed, who triages clinical decisions, and how coverage works during leave.",
            "Confirm remote review of patient-submitted information and digital requests can be routed to qualified clinical staff under organizational privacy and security rules.",
            "Send a test message through each selected channel. Verify it reaches the right queue, receives an owner, and is closed with appropriate documentation.",
        ],
        "deliverable": "A channel and inbox map, patient instructions, coverage assignments, and a test record.",
        "done_when": "A test message reaches a monitored queue and is routed to the right person within the practice’s stated service target.",
        "priority": "Before pilot enrollment",
    },
    {
        "area": "Population review and care gaps",
        "question": "Can the practice use reliable population data to identify care gaps and focus outreach on people who may need more support?",
        "owner": "Quality or population-health lead and health-record/reporting analyst",
        "purpose": "Move from individual referrals alone to a repeatable view of needs across the practice’s panel.",
        "steps": [
            "Choose one population list the practice can produce reliably, such as patients overdue for a defined preventive service. Start with a narrow question rather than a large dashboard.",
            "Write down the list’s data source, definition, refresh date, exclusions, and known data-quality limits. Have a clinician approve the clinical meaning of the measure.",
            "Agree on a transparent prioritization method using organization-approved clinical criteria. Do not use protected traits as a shortcut for deciding who receives care.",
            "Assign each outreach item to a team member and record only the operational status needed in the approved system: attempted, reached, scheduled, declined, or needs clinician review.",
            "Compare the list against a small manual sample to check for missing or outdated records before broad outreach.",
            "Review counts and follow-through at a monthly quality meeting. Ask whether the process is reaching patients equitably and where the data may be incomplete.",
        ],
        "deliverable": "A defined panel list, data-quality note, outreach workflow, and simple monthly review.",
        "done_when": "The team can reproduce the list, explain its definition, assign follow-up, and identify its limitations.",
        "priority": "Build before expanding the pilot",
    },
    {
        "area": "Quality and performance reporting",
        "question": "Has the practice confirmed its applicable CMS performance-measurement and reporting pathway and assigned an owner?",
        "owner": "Quality lead and billing/compliance lead",
        "purpose": "Avoid discovering reporting obligations late or tracking information that the chosen pathway does not use.",
        "steps": [
            "Ask the quality or compliance lead to confirm the practice’s current reporting pathway using current CMS guidance and the practice’s participation status.",
            "Write down which measures, quality activities, cost information, and health-record capabilities must be tracked for that pathway and performance year.",
            "Map each required item to its data source, person responsible, collection frequency, and review meeting. Flag any item the practice cannot produce today.",
            "Create a simple evidence calendar with due dates and an escalation owner. Confirm the plan with the person who submits the organization’s reports.",
            "At the first monthly review, check a sample of the evidence and update the calendar when official instructions change.",
        ],
        "deliverable": "A confirmed reporting pathway, measure/data-source map, and reporting calendar.",
        "done_when": "The report owner can show where each required item comes from and when it will be reviewed or submitted.",
        "priority": "Confirm before pilot",
    },
    {
        "area": "Monthly billing and documentation review",
        "question": "Can the practice reconcile monthly enrollment, documentation, services, and claims with a qualified billing reviewer?",
        "owner": "Billing lead and clinical operations lead",
        "purpose": "Create a routine check for incomplete records, conflicting care-management activity, and claims that need review.",
        "steps": [
            "Have the billing lead maintain a dated reference to current CMS, payer, and Medicare Administrative Contractor instructions. Escalate uncertain code or eligibility decisions rather than embedding assumptions in the planner.",
            "Create a monthly roster reconciliation that checks the responsible billing practitioner, documented consent, eligibility review, applicable initiating-visit review, and required service elements as clinically appropriate.",
            "Add a check for the one-provider-per-patient-per-calendar-month rule and for potentially overlapping care-management billing. Route possible conflicts to a qualified reviewer.",
            "Define who compares the roster with submitted and paid claims, who reviews denials or rejects, and how corrections and staff education are recorded.",
            "Review a small sample each month with the clinical lead and billing lead. Track error themes and update the workflow when official guidance or payer instructions change.",
            "Keep operational financial reporting separate from patient-identifiable details in any portfolio or public reporting.",
        ],
        "deliverable": "A monthly reconciliation checklist, escalation process, and audit log owned by the practice.",
        "done_when": "A reviewer can trace a sample month from roster through documentation review and claim disposition.",
        "priority": "Before first claim",
    },
]


# Federal Register rules behind each planner area (seeds/billing_rules.csv)
AREA_RULES = {
    "Accountable primary-care lead": ["APCM-CODES"],
    "Patient consent and enrollment": ["APCM-CONSENT"],
    "Patient eligibility and initiating-visit check": ["APCM-L1", "APCM-L2", "APCM-L3", "APCM-INITIATING-VISIT"],
    "24/7 access and continuity": ["APCM-247-ACCESS"],
    "Needs assessment and ongoing care management": ["APCM-NO-TIME", "APCM-COORDINATION"],
    "Patient-centered electronic care plan": ["APCM-CARE-PLAN"],
    "Transitions, referrals, and follow-up": ["APCM-TRANSITIONS"],
    "Secure communication options": ["APCM-COORDINATION"],
    "Population review and care gaps": ["APCM-POPULATION"],
    "Quality and performance reporting": ["APCM-PERFORMANCE"],
    "Monthly billing and documentation review": ["APCM-CONCURRENT", "APCM-CONCURRENT-ALLOWED"],
}


def _hints(p: pd.Series | None) -> dict[str, str]:
    """What the practice's visible billing suggests for each area. Hints, never answers."""
    if p is None:
        return {}
    on = lambda k: str(p.get(k)) == "True"
    h = {}
    if on("has_ccm") or on("has_pcm"):
        h["Patient consent and enrollment"] = "Bills CCM or PCM, which also require documented consent. That consent workflow may be reusable."
        h["Patient-centered electronic care plan"] = "Bills CCM or PCM, which require a comprehensive care plan. Start from that template."
        h["Needs assessment and ongoing care management"] = "Already runs monthly care management for some patients."
        h["Monthly billing and documentation review"] = "Bills CCM or PCM today. The APCM practitioner cannot bill them for the same patient in the same month, so plan the switch patient by patient."
    if on("has_awv"):
        h["Patient eligibility and initiating-visit check"] = "Bills wellness visits. An AWV by the APCM practitioner can serve as the initiating visit."
    if on("has_tcm"):
        h["Transitions, referrals, and follow-up"] = "Bills transitional care management, so some discharge follow-up workflow exists."
    if on("has_rpm"):
        h["Secure communication options"] = "Bills remote monitoring, which suggests technology-based patient contact is in place. RPM can continue alongside APCM."
    if on("has_bhi_or_cocm"):
        h["Population review and care gaps"] = "Bills behavioral health integration. BHI can be billed alongside APCM, and 2026 adds APCM behavioral health add-ons (G0568 to G0570)."
    return h


def _practice_by_id(d: dict) -> pd.Series | None:
    pid = st.session_state.get("practice_id")
    if not pid:
        return None
    hit = d["practices"][d["practices"].practice_id == pid]
    return None if hit.empty else hit.iloc[0]


def _planner(d: dict) -> None:
    _band("Build a practical APCM implementation plan",
          "Turn a practice self-check into a sequenced workplan with owners, concrete tasks and completion checks. "
          "Each area cites the Federal Register rule it comes from.", "PRACTICE READINESS PLANNER")
    st.markdown('<div class="note"><b>Planning support only.</b> This tool does not determine patient eligibility, select billing codes, or certify compliance. '
                'Do not enter patient names, IDs, diagnoses, or other private health information. Answers stay in this browser session. '
                'Have your clinical and billing leads verify current requirements with CMS and your payer.</div>', unsafe_allow_html=True)
    rules, p = d["rules"], _practice_by_id(d)
    hints = _hints(p)
    if p is not None:
        with st.expander("Practice this plan is for", expanded=True):
            _profile(p)
            if st.button("Clear practice"):
                st.session_state.pop("practice_id", None)
                st.rerun()
    else:
        st.caption("Tip: pick a practice in the Practice finder to see what its billing already suggests for each area.")

    with st.expander("Set the planning context", expanded=True):
        setting = st.selectbox("What kind of practice are you planning for?", [
            "Independent or small primary-care practice", "Community health center or FQHC",
            "Health system or multisite group", "Other or still deciding"])
        horizon = st.selectbox("When would you like to be ready for a small pilot?", ["Within 30 days", "Within 60 days", "Within 90 days"], index=1)
    notes = {
        "Independent or small primary-care practice": "Keep roles simple: one person may cover more than one task, but name a backup and use an outside billing or compliance partner for unresolved Medicare questions.",
        "Community health center or FQHC": "Include center leadership and the organization's billing lead so the workflow matches the center's operating and payment arrangements. FQHCs and RHCs can bill APCM and, from 2026, the behavioral health add-ons.",
        "Health system or multisite group": "Include enterprise clinical operations, health-record, privacy/security, and revenue-cycle owners; decide which steps are shared and which each site owns.",
    }
    st.info(notes.get(setting, "First confirm which organization owns the billing, clinical oversight, health record, and patient communication workflows."))
    st.write("Answer for the practice's current state. The plan includes only areas marked partly in place, not in place, or needing confirmation.")

    choices = ["In place", "Partly in place", "Not in place", "Need help confirming"]
    with st.form("apcm_readiness_check"):
        answers: dict[str, str | None] = {}
        for idx, item in enumerate(READINESS_QUESTIONS):
            label = item["area"] + (" · billing data has a hint" if item["area"] in hints else "")
            answers[item["area"]] = st.radio(label, choices, index=None, horizontal=True, key=f"readiness_{idx}", help=item["question"])
            if item["area"] in hints:
                st.caption(f"From this practice's 2024 billing: {hints[item['area']]}")
        submitted = st.form_submit_button("Create my implementation plan", type="primary")
    if submitted:
        missing = [a for a, v in answers.items() if v is None]
        if missing:
            st.warning(f"Please answer all {len(READINESS_QUESTIONS)} areas so the workplan reflects the full check.")
            return
        st.session_state["apcm_readiness_answers"] = answers
        st.session_state["apcm_readiness_context"] = {"setting": setting, "horizon": horizon}
    saved = st.session_state.get("apcm_readiness_answers")
    if not saved:
        st.info("Submit the check to get your detailed workplan.")
        return
    ctx = st.session_state.get("apcm_readiness_context", {})
    setting, horizon = ctx.get("setting", setting), ctx.get("horizon", horizon)
    follow = [i for i in READINESS_QUESTIONS if saved.get(i["area"]) != "In place"]
    order = {"Start here": 0, "Before pilot enrollment": 1, "Confirm before pilot": 2, "Before first claim": 3, "Build before expanding the pilot": 4}
    follow.sort(key=lambda i: order.get(i["priority"], 5))
    st.markdown("---")
    st.subheader("Your practice workplan")
    st.write(f"**Setting:** {setting} · **Pilot horizon:** {horizon} · **Focus areas:** {len(follow)} of {len(READINESS_QUESTIONS)}")
    lines = ["# APCM practice implementation plan", f"- Practice setting: {setting}", f"- Target pilot horizon: {horizon}"]
    if p is not None:
        lines.append(f"- Practice: {p.practice_name if isinstance(p.practice_name, str) else p.practice_id} ({p.state}), {int(p.pcp_clinicians)} primary care clinicians, "
                     f"~{p.est_qmb_patients:,.0f} estimated QMB patients, visible 2024 billing: "
                     + (", ".join(v for k, v in SIGNALS.items() if str(p[k]) == "True") or "none"))
    lines += [f"- Focus areas: {len(follow)} of {len(READINESS_QUESTIONS)}", "",
              "Confirm all current CMS, Medicare Administrative Contractor, and payer requirements with the practice's qualified billing/compliance lead. "
              "This workplan is not a code-selection or compliance determination.", ""]
    if not follow:
        st.success("You marked every area in place. Use the completion checks as a maintenance review and confirm current CMS and payer requirements before billing.")
    for n, item in enumerate(follow, start=1):
        ans = saved[item["area"]]
        first = {"Need help confirming": "First confirm the current workflow with the suggested owner and locate an existing policy, record field, or test result. If none exists, use the build steps below.",
                 "Partly in place": "First document what already works and where the handoff breaks; then complete the steps below for the missing pieces."}.get(
                 ans, "Build this workflow with the suggested owner, then test it before using it with a pilot population.")
        cites = [r for r in AREA_RULES.get(item["area"], []) if r in rules.index]
        with st.expander(f"{n}. {item['area']} · {ans} · {item['priority']}", expanded=(n == 1)):
            st.markdown(f"**Why this matters:** {item['purpose']}")
            st.markdown(f"**Suggested owner:** {item['owner']}")
            if item["area"] in hints:
                st.markdown(f"**What billing data suggests:** {hints[item['area']]}")
            st.markdown(f"**First move:** {first}")
            st.markdown("**Step-by-step work**")
            for i, step in enumerate(item["steps"], start=1):
                st.markdown(f"{i}. {step}")
            st.markdown(f"**Create:** {item['deliverable']}")
            st.markdown(f"**Ready to move on when:** {item['done_when']}")
            for r in cites:
                st.markdown(f'<div class="cite"><b>Rule ({rules.loc[r, "federal_register_citation"]}):</b> {rules.loc[r, "interpretation"]}</div>', unsafe_allow_html=True)
        lines += [f"## {n}. {item['area']} ({ans})", f"- Priority: {item['priority']}", f"- Suggested owner: {item['owner']}",
                  f"- Why this matters: {item['purpose']}"]
        if item["area"] in hints:
            lines.append(f"- What billing data suggests: {hints[item['area']]}")
        lines += [f"- First move: {first}", "- Step-by-step work:"] + [f"  {i}. {s}" for i, s in enumerate(item["steps"], start=1)]
        lines += [f"- Create: {item['deliverable']}", f"- Ready to move on when: {item['done_when']}"]
        lines += [f"- Rule ({rules.loc[r, 'federal_register_citation']}): {rules.loc[r, 'interpretation']}" for r in cites] + [""]
    lines += ["## Suggested pilot review",
              "At the end of the pilot horizon, have the clinical lead and billing lead review a small, appropriate sample of workflows and claims. "
              "Record what was completed, what failed, who owns each correction, and when it will be rechecked.", "",
              "## Sources", "- CY2025 PFS final rule, 89 FR 97710 (APCM at 97859-97902)", "- CY2026 PFS final rule (APCM add-ons at 90 FR 49470)",
              "- CMS APCM services: https://www.cms.gov/medicare/payment/fee-schedules/physician-fee-schedule/advanced-primary-care-management-services"]
    st.download_button("Download detailed implementation plan", "\n".join(lines).encode("utf-8"), "apcm_practice_implementation_plan.md", "text/markdown")
    st.caption("The plan gives workflow ideas and completion checks. It does not replace the practice's CMS, payer, clinical, privacy, or billing review.")


# ------------------------------------------------------------------ payment calculator
def _calculator(d: dict) -> None:
    _band("What could APCM pay a practice?", "A what-if calculator using CMS's real 2026 payment amounts for your Medicare locality. "
          "You set the patient numbers; nothing here is a forecast for a real practice.", "PAYMENT CALCULATOR · CY2026 RATES")
    rates = d["locality_rates"]
    nat = d["fee_schedule_2026"].query("cf_type == 'nonqpp'").set_index("hcpcs").national_nonfac_amount
    locs = rates.drop_duplicates(["mac", "locality"]).assign(label=lambda x: x.locality_name.str.title() + " (" + x.mac + "-" + x.locality + ")").sort_values("label")
    p = _practice_by_id(d)
    c = st.columns([1.4, 1])
    loc = c[0].selectbox("Medicare payment locality", ["National amount (no geographic adjustment)"] + list(locs.label))
    setting = c[1].radio("Setting", ["Office (non-facility)", "Facility"], horizontal=True)
    col = "cms_nonfac" if setting.startswith("Office") else "cms_fac"
    if loc.startswith("National"):
        fee = d["fee_schedule_2026"].query("cf_type == 'nonqpp'").set_index("hcpcs")["national_nonfac_amount" if col == "cms_nonfac" else "national_fac_amount"]
        r = {k: float(fee[k]) for k in ["G0556", "G0557", "G0558", "99490"]}
    else:
        m = locs.loc[locs.label == loc].iloc[0]
        sel = rates[(rates.mac == m.mac) & (rates.locality == m.locality)].set_index("hcpcs")[col]
        r = {k: float(sel[k]) for k in ["G0556", "G0557", "G0558", "99490"]}
    if p is not None:
        st.caption(f"Starting from {p.practice_name if isinstance(p.practice_name, str) else p.practice_id}: {int(p.patient_panel_proxy):,} Medicare patients "
                   f"(summed across clinicians) and ~{p.est_qmb_patients:,.0f} estimated QMB patients. Adjust to your own panel.")
    default_panel = int(min(p.patient_panel_proxy, 50000)) if p is not None else 1500
    default_qmb = float(min(p.est_qmb_patients / p.patient_panel_proxy, 1)) if p is not None and p.patient_panel_proxy and pd.notna(p.est_qmb_patients) else 0.15
    i = st.columns(3)
    panel = i[0].number_input("Traditional Medicare patients", 0, 500000, default_panel, step=100)
    qmb = i[1].slider("Share who are QMBs", 0.0, 1.0, round(default_qmb, 2), 0.01, format="%.2f")
    enrolled = i[2].slider("Share enrolled in APCM (capture x consent)", 0.0, 1.0, 0.19, 0.01, format="%.2f",
                           help="The national base scenario uses 25% capture x 75% consent = 19%.")
    j = st.columns(2)
    multi_q = j[0].slider("QMB patients with 2+ qualifying conditions", 0.0, 1.0, 0.80, 0.05)
    multi_o = j[1].slider("Other patients with 2+ qualifying conditions", 0.0, 1.0, 0.65, 0.05)
    n = panel * enrolled
    months = {"G0558": n * qmb * multi_q, "G0557": n * (1 - qmb) * multi_o, "G0556": n * (qmb * (1 - multi_q) + (1 - qmb) * (1 - multi_o))}
    monthly = {k: v * r[k] for k, v in months.items()}
    total_m = sum(monthly.values())
    coins = 0.2 * (monthly["G0557"] + n * (1 - qmb) * (1 - multi_o) * r["G0556"])
    m = st.columns(4)
    m[0].metric("Enrolled patients", f"{n:,.0f}")
    m[1].metric("Allowed per month", _money(total_m))
    m[2].metric("Allowed per year", _money(12 * total_m))
    m[3].metric("Patient coinsurance per year", _money(12 * coins), help="20% for non-QMB patients; QMBs owe no Medicare cost sharing (89 FR 97875).")
    t = pd.DataFrame({"Level": ["G0556 (0-1 conditions)", "G0557 (2+ conditions)", "G0558 (QMB, 2+ conditions)"],
                      "Patients": [months["G0556"], months["G0557"], months["G0558"]],
                      "Rate per month": [r["G0556"], r["G0557"], r["G0558"]],
                      "Allowed per year": [12 * monthly["G0556"], 12 * monthly["G0557"], 12 * monthly["G0558"]]})
    st.dataframe(t.style.format({"Patients": "{:,.0f}", "Rate per month": "${:,.2f}", "Allowed per year": "${:,.0f}"}), hide_index=True, width="stretch")
    st.write(_md(f"For comparison, billing base CCM (99490, ${r['99490']:.2f}) for the same {months['G0557'] + months['G0558']:,.0f} patients with 2+ conditions "
             f"in every month would be {_money(12 * r['99490'] * (months['G0557'] + months['G0558']))} a year, but each month needs 20 documented minutes. "
             "The median 2024 CCM biller billed 4.5 months per patient."))
    st.caption("Rates: CMS National Payment Amount File 2026 (non-QP). Allowed amount includes the patient's share. The practitioner billing APCM cannot bill CCM, PCM or TCM for the same patient in the same month (89 FR 97896).")


# ------------------------------------------------------------------ app
VIEWS = ["National findings", "Practice finder", "Plan APCM next steps", "Payment calculator"]


def main(root: Path) -> None:
    st.set_page_config(page_title="APCM Readiness Atlas", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
    _style()
    d = _load(str(root))
    if "nav_target" in st.session_state:  # set by buttons; applied before the radio is drawn
        st.session_state["view"] = st.session_state.pop("nav_target")
    with st.sidebar:
        st.markdown("### APCM Readiness Atlas")
        st.caption("Medicare · primary care · real CMS data")
        view = st.radio("Choose a view", VIEWS, key="view")
        st.markdown("---")
        st.caption("Built from CMS, HRSA, CDC and Census public files with a reproducible pipeline. "
                   f"[Full report]({ATLAS}) · [Code and methods]({REPO})")
    {"National findings": _findings, "Practice finder": _finder, "Plan APCM next steps": _planner, "Payment calculator": _calculator}[view](d)
