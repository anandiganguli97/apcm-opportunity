"""Presentation layer. Analysis rules live in the data and warehouse layers."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

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


@st.cache_resource(show_spinner=False)
def _ensure_public_data(root_path: str) -> tuple[bool, str]:
    root = Path(root_path)
    processed = root / "data/public_processed/cms_provider_readiness_2024.csv"
    manifest = root / "data/public_raw/cms_provider_service_2024_manifest.json"
    if processed.exists():
        return True, ""
    try:
        download = subprocess.run(
            [sys.executable, str(root / "scripts/download_public_provider_use.py"), "--year", "2024"],
            cwd=root, capture_output=True, text=True, check=True, timeout=900,
        )
        build = subprocess.run(
            [sys.executable, str(root / "scripts/build_public_readiness.py"), "--year", "2024"],
            cwd=root, capture_output=True, text=True, check=True, timeout=300,
        )
        return processed.exists() and manifest.exists(), (download.stdout + "\n" + build.stdout)[-4000:]
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        output = getattr(exc, "stdout", "") or ""
        error = getattr(exc, "stderr", "") or str(exc)
        return False, (output + "\n" + error)[-4000:]


def _public_dashboard(processed: Path, raw_manifest: Path) -> None:
    _hero("Where care-management experience already exists", "A national look at Medicare providers’ past billing for services related to APCM.", "CMS PUBLIC DATA · 2024")
    if not processed.exists():
        st.warning("The results file is missing. Follow the refresh steps in the project README.")
        st.code("python scripts/download_public_provider_use.py --year 2024\npython scripts/build_public_readiness.py --year 2024", language="bash")
        st.stop()

    frame = pd.read_csv(processed, dtype={"provider_npi": str, "zip5": str, "ruca_code": str})
    metadata = {}
    if raw_manifest.exists():
        import json
        metadata = json.loads(raw_manifest.read_text(encoding="utf-8"))
    visible_signal = int(frame["observed_care_management_families"].gt(0).sum())
    multi_family = int(frame["observed_care_management_families"].ge(2).sum())
    ruca_observed = int(frame["ruca_code"].fillna("").astype(str).ne("").sum())
    total_services = int(frame["service_volume_units"].fillna(0).sum())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Providers with a visible signal", f"{visible_signal:,}", help="NPIs with a published, nonzero row for at least one selected prior-care-management service.")
    m2.metric("Providers billing 2+ service types", f"{multi_family:,}", help="NPIs with visible rows in two or more prior-care-management families.")
    m3.metric("Care-management service units", f"{total_services:,}", help="CMS-reported service units summed across selected care-management codes and place of service; not unique patients or months.")
    m4.metric("NPIs with RUCA code", f"{ruca_observed:,}", help="A rural-urban classification code is present. This view does not infer a service area from the NPI address.")
    st.markdown('<div class="note"><b>What this can tell us:</b> where providers have visible experience with related services. <b>What it cannot tell us:</b> which patients qualify for APCM, whether a practice is ready, or how much it could earn. CMS suppresses some low-volume records, so a missing row does not always mean no service was provided.</div>', unsafe_allow_html=True)

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

    st.markdown("### Why this matters for public health")
    st.write("APCM is a new way for Medicare to support ongoing primary care. A provider’s past billing for related services can help describe the starting landscape, but it is only one clue. These results can guide better questions about implementation support and where more detailed data are needed.")
    st.markdown("Read the [headline findings and plain-language interpretation](https://github.com/anandiganguli97/apcm-opportunity/blob/main/docs/results.md).")

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
    display_names = {"provider_npi": "Provider NPI", "provider_type": "Provider type", "state": "State", "zip5": "ZIP code", "ruca_code": "Rural-urban code", "observed_care_management_families": "Service types observed", "readiness_breadth_index": "Billing breadth (0–100)", "service_volume_units": "Reported service units"}
    st.dataframe(visible[display_cols].rename(columns=display_names).sort_values("Reported service units", ascending=False).head(1000), hide_index=True, use_container_width=True, height=420)
    st.caption(f"Showing up to 1,000 of {len(visible):,} matching provider NPIs. Download the visible aggregate table below for local review.")
    st.download_button("Download filtered provider table", visible[display_cols].to_csv(index=False).encode("utf-8"), file_name="apcm_provider_readiness_2024.csv", mime="text/csv")
    st.subheader("Equity question: what this file can and cannot answer")
    st.write("The rural-urban code supports an initial geographic comparison of provider billing history. This file does not include enough patient-level detail to tell which communities have more people who could qualify for APCM or whether those patients are being reached. A fair comparison needs more detailed, carefully protected data.")
    if metadata:
        with st.expander("Source and refresh details"):
            st.write({"source": metadata.get("source"), "reporting year": metadata.get("reporting_year"), "dataset UUID": metadata.get("dataset_uuid"), "API rows downloaded": metadata.get("row_count"), "retrieved UTC": metadata.get("retrieved_utc")})


READINESS_QUESTIONS = [
    {
        "area": "A named primary-care lead",
        "question": "Does the practice have a clinician who is responsible for coordinating each participating patient’s primary care and directing the care team?",
        "action": "Identify the accountable clinician and a coverage plan so patients and staff know who coordinates care.",
    },
    {
        "area": "Patient consent",
        "question": "Can the practice explain APCM, get and document consent before services begin, and explain that patients may stop at any time and cost sharing may apply?",
        "action": "Create a short consent conversation and a consistent place in the record to document it, including the one-practitioner-per-month rule and possible cost sharing.",
    },
    {
        "area": "Initiating visits",
        "question": "Does the team know when a patient needs an initiating visit before APCM starts, and how to check the applicable exceptions?",
        "action": "Add a simple initiating-visit check to the enrollment workflow and confirm it against current CMS guidance.",
    },
    {
        "area": "Access and continuity",
        "question": "Can patients or caregivers reach the care team for urgent needs at all hours, and can the team access current patient information and arrange ongoing appointments?",
        "action": "Document the after-hours route, record-access process, and continuity plan; test the route with staff.",
    },
    {
        "area": "Assessment and care plans",
        "question": "Can the practice assess medical and social needs, support medication management, and maintain a patient-centered care plan that the patient and care team can access?",
        "action": "Agree on a care-plan template, who updates it, how the patient receives a copy, and how the team reviews needs and medications.",
    },
    {
        "area": "Transitions and referrals",
        "question": "Does the practice track referrals and transitions from emergency departments, hospitals, and other settings, with timely patient follow-up when clinically appropriate?",
        "action": "Create a transition queue with an owner, a way to receive discharge information, and a process to contact patients within the CMS timeframe when indicated.",
    },
    {
        "area": "Communication options",
        "question": "Can patients communicate with the practice through secure options beyond the telephone, and can clinicians review patient-submitted information when needed?",
        "action": "Choose a secure non-phone communication route and define who reviews incoming messages and how quickly they are routed.",
    },
    {
        "area": "Finding care gaps",
        "question": "Can the practice review its patient population to identify care gaps and patients who may need more support?",
        "action": "Start with one reliable EHR or claims-based list, such as overdue preventive care, and assign someone to review and act on it.",
    },
    {
        "area": "Quality reporting",
        "question": "Has the practice confirmed its quality-reporting pathway and who owns reporting and follow-through?",
        "action": "Ask the practice’s quality lead or billing partner to confirm which CMS reporting pathway applies and what must be tracked.",
    },
    {
        "area": "Monthly billing review",
        "question": "Is there a process to review APCM claims each month and coordinate with the care team so only the appropriate practitioner bills for a patient in a calendar month?",
        "action": "Set up a monthly review with the billing lead to check eligibility documentation, consent, required services, and possible duplicate billing.",
    },
]


def _readiness_planner() -> None:
    _hero(
        "Plan your next APCM steps",
        "A practical self-check for primary-care teams preparing to deliver ongoing, coordinated care.",
        "PRACTICE READINESS PLANNER",
    )
    st.markdown(
        '<div class="note"><b>This is a planning aid, not a compliance review or billing recommendation.</b> '
        'Do not enter patient names, IDs, diagnoses, or other private health information. '
        'Your answers are used only to create this session’s action plan and are not saved by this project.</div>',
        unsafe_allow_html=True,
    )
    st.write("For each area, choose the answer that best describes the practice today. The plan will point to practical follow-up steps; it will not calculate a readiness score.")

    answer_choices = ["In place", "Partly in place", "Not in place", "Need help confirming"]
    with st.form("apcm_readiness_check"):
        answers: dict[str, str | None] = {}
        for idx, item in enumerate(READINESS_QUESTIONS):
            answers[item["area"]] = st.radio(
                item["area"], answer_choices, index=None, horizontal=True,
                key=f"readiness_{idx}", help=item["question"],
            )
        submitted = st.form_submit_button("Create my next-step plan", type="primary")

    if submitted:
        unanswered = [area for area, answer in answers.items() if answer is None]
        if unanswered:
            st.warning(f"Please choose an answer for all {len(READINESS_QUESTIONS)} areas so the plan reflects your full check.")
            return
        st.session_state["apcm_readiness_answers"] = answers

    saved_answers = st.session_state.get("apcm_readiness_answers")
    if not saved_answers:
        st.info("Your answers remain in this browser session. Submit the check to see a tailored action plan.")
        return

    follow_up = [item for item in READINESS_QUESTIONS if saved_answers.get(item["area"]) != "In place"]
    st.subheader("Your next steps")
    if not follow_up:
        st.success("You marked all areas as in place. Keep the workflows current and review them with your clinical and billing leads against current CMS guidance.")
        plan_lines = ["APCM practice planning summary", "All areas marked in place; continue routine review against current CMS guidance."]
    else:
        st.write(f"You identified **{len(follow_up)} area(s)** to confirm or strengthen. Start with the steps below.")
        plan_lines = ["APCM practice planning summary", "Areas to follow up:"]
        for item in follow_up:
            answer = saved_answers[item["area"]]
            st.markdown(f"**{item['area']} · {answer}**\n\n{item['action']}")
            plan_lines.append(f"- {item['area']} ({answer}): {item['action']}")
    st.download_button(
        "Download my action plan",
        "\n".join(plan_lines).encode("utf-8"),
        file_name="apcm_practice_next_steps.txt",
        mime="text/plain",
    )
    st.markdown("For the full service requirements, review the [current CMS APCM guidance](https://www.cms.gov/medicare/payment/fee-schedules/physician-fee-schedule/advanced-primary-care-management-services).")


def main(root: Path) -> None:
    st.set_page_config(page_title="APCM Opportunity Lab", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
    _style()
    with st.sidebar:
        st.markdown("### APCM Opportunity Lab")
        st.caption("Medicare · primary care · public evidence")
        view = st.radio("Choose a tool", ["Explore public data", "Plan APCM next steps"], index=0)
        st.markdown("---")
        if view == "Explore public data":
            st.caption("Source: CMS public Medicare data, 2024. Results describe provider billing history, not patient eligibility.")
        else:
            st.caption("Self-assessment only. Do not enter patient information.")
    if view == "Plan APCM next steps":
        _readiness_planner()
        return
    processed = root / "data/public_processed/cms_provider_readiness_2024.csv"
    manifest = root / "data/public_raw/cms_provider_service_2024_manifest.json"
    if not processed.exists():
        with st.spinner("Loading public CMS data for the first time. This may take a few minutes…"):
            ready, log = _ensure_public_data(str(root))
        if not ready:
            st.error("The CMS data could not be loaded right now. Please refresh later, or follow the local refresh steps in the project README.")
            with st.expander("Details for troubleshooting"):
                st.code(log or "No error details were returned.")
            st.stop()
    _public_dashboard(processed, manifest)

