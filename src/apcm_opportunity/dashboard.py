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


def _readiness_planner() -> None:
    _hero(
        "Build a practical APCM implementation plan",
        "Turn a practice self-check into a sequenced workplan with owners, concrete tasks, and completion checks.",
        "PRACTICE READINESS PLANNER",
    )
    st.markdown(
        '<div class="note"><b>Planning support only.</b> This tool does not determine patient eligibility, select billing codes, or certify compliance. '
        'Do not enter patient names, IDs, diagnoses, or other private health information. Answers stay in this browser session and are not saved by this project. '
        'Have your clinical and billing leads verify current requirements with CMS and your payer.</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Set the planning context", expanded=True):
        setting = st.selectbox(
            "What kind of practice are you planning for?",
            [
                "Independent or small primary-care practice",
                "Community health center or FQHC",
                "Health system or multisite group",
                "Other or still deciding",
            ],
        )
        horizon = st.selectbox(
            "When would you like to be ready for a small pilot?",
            ["Within 30 days", "Within 60 days", "Within 90 days"],
            index=1,
        )

    if setting == "Independent or small primary-care practice":
        context_note = "Keep roles simple: one person may cover more than one task, but name a backup and use an outside billing or compliance partner for unresolved Medicare questions."
    elif setting == "Community health center or FQHC":
        context_note = "Include center leadership and the organization’s billing lead so the workflow matches the center’s operating and payment arrangements."
    elif setting == "Health system or multisite group":
        context_note = "Include enterprise clinical operations, health-record, privacy/security, and revenue-cycle owners; decide which steps are shared and which each site owns."
    else:
        context_note = "First confirm which organization owns the billing, clinical oversight, health record, and patient communication workflows."
    st.info(context_note)
    st.write("Answer for the practice’s current state. The plan will include only areas marked partly in place, not in place, or needing confirmation.")

    answer_choices = ["In place", "Partly in place", "Not in place", "Need help confirming"]
    with st.form("apcm_readiness_check"):
        answers: dict[str, str | None] = {}
        for idx, item in enumerate(READINESS_QUESTIONS):
            answers[item["area"]] = st.radio(
                item["area"], answer_choices, index=None, horizontal=True,
                key=f"readiness_{idx}", help=item["question"],
            )
        submitted = st.form_submit_button("Create my implementation plan", type="primary")

    if submitted:
        unanswered = [area for area, answer in answers.items() if answer is None]
        if unanswered:
            st.warning(f"Please answer all {len(READINESS_QUESTIONS)} areas so the workplan reflects the full check.")
            return
        st.session_state["apcm_readiness_answers"] = answers
        st.session_state["apcm_readiness_context"] = {"setting": setting, "horizon": horizon}

    saved_answers = st.session_state.get("apcm_readiness_answers")
    saved_context = st.session_state.get("apcm_readiness_context", {})
    if not saved_answers:
        st.info("Your answers stay in this browser session. Submit the check to get your detailed workplan.")
        return

    setting = saved_context.get("setting", setting)
    horizon = saved_context.get("horizon", horizon)
    follow_up = [item for item in READINESS_QUESTIONS if saved_answers.get(item["area"]) != "In place"]
    st.markdown("---")
    st.subheader("Your practice workplan")
    st.write(f"**Setting:** {setting} · **Pilot horizon:** {horizon}")
    st.write(f"**Focus areas:** {len(follow_up)} of {len(READINESS_QUESTIONS)} need action or confirmation.")
    st.write("Start with the pre-pilot items. Build the workflow, test it with fictional or de-identified examples, then review the first month with clinical and billing leads.")

    if not follow_up:
        st.success("You marked every area in place. Use the completion checks below as a maintenance review and confirm the current CMS and payer requirements before billing.")
        plan_lines = [
            "# APCM practice implementation plan",
            f"- Practice setting: {setting}",
            f"- Pilot horizon: {horizon}",
            "",
            "All areas were marked in place. Use this plan as a maintenance review and confirm current CMS and payer requirements.",
        ]
    else:
        priority_order = {"Start here": 0, "Before pilot enrollment": 1, "Confirm before pilot": 2, "Before first claim": 3, "Build before expanding the pilot": 4}
        follow_up.sort(key=lambda item: priority_order.get(item["priority"], 5))
        plan_lines = [
            "# APCM practice implementation plan",
            f"- Practice setting: {setting}",
            f"- Target pilot horizon: {horizon}",
            f"- Focus areas: {len(follow_up)} of {len(READINESS_QUESTIONS)}",
            "",
            "## Before pilot or first claim",
            "Confirm all current CMS, Medicare Administrative Contractor, and payer requirements with the practice’s qualified billing/compliance lead. This workplan is not a code-selection or compliance determination.",
            "",
        ]
        for number, item in enumerate(follow_up, start=1):
            answer = saved_answers[item["area"]]
            if answer == "Need help confirming":
                first_step = "First confirm the current workflow with the suggested owner and locate an existing policy, record field, or test result. If none exists, use the build steps below."
            elif answer == "Partly in place":
                first_step = "First document what already works and where the handoff breaks; then complete the steps below for the missing pieces."
            else:
                first_step = "Build this workflow with the suggested owner, then test it before using it with a pilot population."
            with st.expander(f"{number}. {item['area']} · {answer} · {item['priority']}", expanded=(number == 1)):
                st.markdown(f"**Why this matters:** {item['purpose']}")
                st.markdown(f"**Suggested owner:** {item['owner']}")
                st.markdown(f"**First move:** {first_step}")
                st.markdown("**Step-by-step work**")
                for step_number, step in enumerate(item["steps"], start=1):
                    st.markdown(f"{step_number}. {step}")
                st.markdown(f"**Create:** {item['deliverable']}")
                st.markdown(f"**Ready to move on when:** {item['done_when']}")
            plan_lines.extend([
                f"## {number}. {item['area']} ({answer})",
                f"- Priority: {item['priority']}",
                f"- Suggested owner: {item['owner']}",
                f"- Why this matters: {item['purpose']}",
                f"- First move: {first_step}",
                "- Step-by-step work:",
            ])
            plan_lines.extend([f"  {step_number}. {step}" for step_number, step in enumerate(item["steps"], start=1)])
            plan_lines.extend([
                f"- Create: {item['deliverable']}",
                f"- Ready to move on when: {item['done_when']}",
                "",
            ])
        plan_lines.extend([
            "## Suggested pilot review",
            "At the end of the selected pilot horizon, have the clinical lead and billing lead review a small, appropriate sample of workflows and claims. Record what was completed, what failed, who owns each correction, and when it will be rechecked. Use approved systems for any patient-level review.",
            "",
            "## Source",
            "CMS Advanced Primary Care Management Services: https://www.cms.gov/medicare/payment/fee-schedules/physician-fee-schedule/advanced-primary-care-management-services",
        ])

    st.download_button(
        "Download detailed implementation plan",
        "\n".join(plan_lines).encode("utf-8"),
        file_name="apcm_practice_implementation_plan.md",
        mime="text/markdown",
    )
    st.caption("The plan provides workflow ideas and completion checks. It does not replace the practice’s current CMS, payer, clinical, privacy, or billing review.")
    st.markdown("Use the [current CMS APCM service requirements](https://www.cms.gov/medicare/payment/fee-schedules/physician-fee-schedule/advanced-primary-care-management-services) and confirm payer-specific rules with the practice’s qualified billing lead.")

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

