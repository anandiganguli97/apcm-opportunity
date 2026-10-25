"""Headless checks of the Streamlit app against the committed pipeline outputs."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def run(view: str | None = None, **state) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if view:
        at.sidebar.radio(key="view").set_value(view).run()
    assert not at.exception, at.exception
    return at


def test_findings_loads_with_real_numbers():
    at = run()
    labels = [m.label for m in at.metric]
    assert "Primary care clinicians" in labels
    assert at.metric[0].value == "215,245"


def test_every_view_renders():
    for view in ["Practice finder", "Plan APCM next steps", "Payment calculator"]:
        run(view)


def test_planner_builds_workplan_for_a_practice():
    import pandas as pd
    first = pd.read_csv(Path(APP).parent / "pipeline_output/results/practice_extract_tableau.csv.gz", dtype={"practice_id": str}, nrows=1)
    at = run("Plan APCM next steps", practice_id=first.practice_id.iloc[0])
    for i in range(11):
        at.radio(key=f"readiness_{i}").set_value("In place" if i == 3 else "Not in place")
    next(b for b in at.button if b.label == "Create my implementation plan").click().run()
    assert not at.exception, at.exception
    assert any("Your practice workplan" in s.value for s in at.subheader)
    # ten areas need work; each cites its Federal Register rule
    assert len([e for e in at.expander if e.label[:2].rstrip(".").isdigit()]) == 10
    assert any("FR" in m.value for m in at.markdown if "Rule (" in m.value)


def test_calculator_matches_rates():
    at = run("Payment calculator")
    at.number_input[0].set_value(1000).run()
    for s in at.slider:
        if s.label.startswith("Share who are QMBs"):
            s.set_value(0.0)
        if s.label.startswith("Share enrolled"):
            s.set_value(1.0)
        if s.label.startswith("Other patients"):
            s.set_value(1.0)
    at.run()
    assert not at.exception, at.exception
    # 1,000 non-QMB patients, all with 2+ conditions, all enrolled -> 1,000 x G0557 x 12
    per_year = [m.value for m in at.metric if m.label == "Allowed per year"][0]
    assert per_year == "$645,360", per_year


def test_npi_search_finds_the_clinicians_practice():
    import pandas as pd
    root = Path(APP).parent / "pipeline_output/results"
    lookup = pd.read_csv(root / "npi_practice_lookup.csv.gz", dtype={"npi": str, "practice_id": str}, nrows=50)
    row = lookup[~lookup.practice_id.str.startswith("npi:")].iloc[0]
    at = run("Practice finder")
    at.text_input[0].set_value(row.npi).run()
    assert not at.exception, at.exception
    shown = at.dataframe[0].value
    assert list(shown["Practice ID"]) == [row.practice_id]


def test_frozen_forecast_is_unchanged():
    """The 2025 forecast of record must match the hashes written when it was frozen."""
    import hashlib
    import json
    frozen = Path(APP).parent / "pipeline_output/forecast/frozen_2025_v1"
    for name in ["apcm_2025_predictions.csv.gz", "model_card.json"]:
        manifest = json.loads((frozen / f"{name}.json").read_text())
        assert manifest["frozen_at_utc"] == "2026-10-25T04:35:06Z"
        assert hashlib.sha256((frozen / name).read_bytes()).hexdigest() == manifest["sha256"], name
