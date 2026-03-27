from __future__ import annotations

import json
import time

import streamlit as st
from dotenv import load_dotenv

from src.schemas import VehicleQuery
from src.workflow import run_automotive_crew


st.set_page_config(page_title="Multi-Agent Automotive System", page_icon="🚗", layout="wide")

load_dotenv()

st.markdown(
    """
    <div style="text-align:center; margin-top: 0.25rem;">
      <div style="font-size: 2.2rem; font-weight: 850; line-height: 1.1;">🚗 Multi-Agent Automotive System</div>
      <div style="font-size: 1.05rem; opacity: 0.85; margin-top: 0.35rem;">Get car specifications and insights using AI</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

if "vehicle_query" not in st.session_state:
    st.session_state.vehicle_query = ""
if "last_error" not in st.session_state:
    st.session_state.last_error = None


def _set_example(q: str) -> None:
    st.session_state.vehicle_query = q


with st.container(border=True):
    st.markdown("### Enter vehicle")
    vehicle_query = st.text_input(
        label="Enter vehicle",
        value=st.session_state.vehicle_query,
        placeholder="e.g., Toyota Camry 2024 India",
        label_visibility="collapsed",
        key="vehicle_query",
    )

    st.markdown("<div style='height: 0.25rem;'></div>", unsafe_allow_html=True)
    st.caption("Try an example:")
    ex1, ex2, ex3 = st.columns(3)
    ex1.button("Toyota Camry 2024", use_container_width=True, on_click=_set_example, args=("Toyota Camry 2024",))
    ex2.button(
        "Hyundai Creta diesel India",
        use_container_width=True,
        on_click=_set_example,
        args=("Hyundai Creta diesel India",),
    )
    ex3.button(
        "Tesla Model 3 performance",
        use_container_width=True,
        on_click=_set_example,
        args=("Tesla Model 3 performance",),
    )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    run_btn = st.button("Analyze Vehicle", type="primary", use_container_width=True)
    clear_btn = st.button("Clear", use_container_width=True)

if clear_btn:
    st.session_state.vehicle_query = ""
    st.session_state.last_error = None
    st.rerun()

st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

if not run_btn:
    st.markdown(
        "<div style='text-align:center; opacity: 0.8; font-size: 1.05rem;'>Enter a vehicle above to get started 🚗</div>",
        unsafe_allow_html=True,
    )

if run_btn:

    if not vehicle_query.strip():
        st.error("Please enter a vehicle name")
        st.stop()

    v = VehicleQuery(
        query=vehicle_query.strip(),
    )

    try:
        start_time = time.time()
        progress = st.empty()
        with st.spinner("Analyzing vehicle using AI agents..."):
            progress.info("Data collection: Researching vehicle data...")
            out = run_automotive_crew(v)
            progress.info("Report generation: Generating report...")
        progress.empty()
        execution_time = round(time.time() - start_time, 2)
        st.session_state.last_error = None
    except Exception as e:
        st.session_state.last_error = str(e)
        st.error("Something went wrong. Please try again.")
        out = None
        execution_time = None

    if out is None:
        tab_report, tab_sources, tab_debug = st.tabs(["📊 Report", "🔗 Sources", "🧠 Debug"])
        with tab_report:
            st.info("No report available.")
        with tab_sources:
            st.info("No sources available.")
        with tab_debug:
            st.markdown("### Debug")
            st.code(st.session_state.last_error or "Unknown error")
        st.stop()

    origin = (out.meta or {}).get("source_origin", "unknown")
    if origin == "cache":
        st.info("⚡ Loaded from cache")
    elif origin == "web":
        st.info("🌐 Fetched from web")

    st.success(f"⏱️ Analysis completed in {execution_time} seconds")

    tab_report, tab_sources, tab_debug = st.tabs(["📊 Report", "🔗 Sources", "🧠 Debug"])

    with tab_report:
        st.subheader(out.title)
        st.markdown(out.markdown_report)

    with tab_sources:
        if out.citations:
            for i, s in enumerate(out.citations, 1):
                st.markdown(f"{i}. [{s.title}]({s.url})")
                if s.snippet:
                    st.caption(s.snippet)
        else:
            st.info("No sources available.")

    with tab_debug:
        st.markdown("### Research brief (JSON)")
        st.json(out.brief.model_dump())
        st.markdown("### Full JSON dump")
        st.code(json.dumps(out.brief.model_dump(), indent=2, ensure_ascii=False), language="json")
        if st.session_state.last_error:
            st.markdown("### Last error")
            st.code(st.session_state.last_error)

    # Download
    st.download_button(
        "📥 Download Report (Markdown)",
        data=out.markdown_report.encode("utf-8"),
        file_name=f"{out.title.replace(' ', '_')}.md",
        mime="text/markdown",
    )