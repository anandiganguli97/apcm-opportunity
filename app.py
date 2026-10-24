"""Thin Streamlit entry point for the APCM analysis surfaces."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

# Load the dashboard module directly. This avoids package-name resolution issues
# in Streamlit Community Cloud's isolated script loader.
DASHBOARD_PATH = SRC / "apcm_opportunity" / "dashboard.py"
spec = spec_from_file_location("apcm_dashboard", DASHBOARD_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load dashboard module from {DASHBOARD_PATH}")
dashboard = module_from_spec(spec)
sys.modules[spec.name] = dashboard
spec.loader.exec_module(dashboard)

dashboard.main(ROOT)
