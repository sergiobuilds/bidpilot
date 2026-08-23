"""BidPilot — the pursuit workspace entry point.

The whole product is four stages over one analysis that Snowflake already
recorded. This script only configures the page and hands over to the
presentation layer, which reads that analysis through the reader connection
named by BIDPILOT_SNOWFLAKE_CONNECTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

SOURCE_ROOT = Path(__file__).parent / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from bidpilot import refinement_app

st.set_page_config(
    page_title="BidPilot — pursuit workspace",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

refinement_app.render()
