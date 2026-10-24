"""Thin Streamlit entry point for the APCM analysis surfaces."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from apcm_opportunity.dashboard import main

main(ROOT)

