from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from src.ui.styles import inject_styles, render_header, render_footer
from src.ui.research import render_research_tab
from src.ui.concept import render_concept_tab
from src.ui.compare import render_compare_tab

load_dotenv()

st.set_page_config(
    page_title="AutoVerse AI",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_styles()
render_header()

tab1, tab2, tab3 = st.tabs([
    "Research",
    "Design",
    "Compare",
])

with tab1:
    render_research_tab()

with tab2:
    render_concept_tab()

with tab3:
    render_compare_tab()

render_footer()
