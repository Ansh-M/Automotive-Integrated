from __future__ import annotations
import re
import time
import streamlit as st
from src.schemas import VehicleQuery
from src.workflow import run_automotive_crew


def _md_table_to_html(md: str) -> str:
    """Convert any markdown pipe tables in a report to HTML tables so
    Streamlit renders them correctly via unsafe_allow_html=True."""

    table_pattern = re.compile(
        r'((?:\|.*\|\n)+)',
        re.MULTILINE
    )

    def convert_table(match: re.Match) -> str:
        raw = match.group(1).strip()
        rows = [r.strip() for r in raw.split("\n") if r.strip()]

        # filter out separator rows like |---|---|
        data_rows = [r for r in rows if not re.match(r'^\|[\s\-|:]+\|$', r)]

        if len(data_rows) < 1:
            return match.group(0)

        def parse_row(row: str) -> list[str]:
            return [c.strip() for c in row.strip("|").split("|")]

        header = parse_row(data_rows[0])
        body = data_rows[1:]

        th = "".join(f"<th style='padding:8px 12px;border:1px solid #374151;background:#1f2937;color:#f9fafb;text-align:left'>{h}</th>" for h in header)
        thead = f"<thead><tr>{th}</tr></thead>"

        tbody_rows = ""
        for i, row in enumerate(body):
            cells = parse_row(row)
            bg = "#111827" if i % 2 == 0 else "#1a2332"
            td = "".join(f"<td style='padding:8px 12px;border:1px solid #374151;color:#e5e7eb'>{c}</td>" for c in cells)
            tbody_rows += f"<tr style='background:{bg}'>{td}</tr>"

        tbody = f"<tbody>{tbody_rows}</tbody>"
        return f"<div style='overflow-x:auto;margin:1rem 0'><table style='border-collapse:collapse;width:100%;font-size:0.9rem'>{thead}{tbody}</table></div>\n"

    return table_pattern.sub(convert_table, md)


def render_research_tab() -> None:
    st.markdown("### Research any car — powered by AI agents")
    st.caption("Two AI agents (Researcher + Writer) fetch live web data, synthesize specs, and generate a structured report.")

    with st.container(border=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            vehicle_query = st.text_input(
                "Vehicle",
                placeholder="e.g. Hyundai Creta 2024 India, BMW M4 Competition, Tesla Model 3",
                label_visibility="collapsed",
                key="research_query",
            )
        with col_btn:
            research_btn = st.button("Analyze", type="primary", use_container_width=True)

        st.caption("Quick examples:")
        ec1, ec2, ec3, ec4 = st.columns(4)
        examples = [
            ("Hyundai Creta 2024", "Hyundai Creta 2024 India"),
            ("Tata Nexon EV", "Tata Nexon EV 2024"),
            ("BMW M4 Competition", "BMW M4 Competition 2024"),
            ("Mahindra XUV700", "Mahindra XUV700 2024 India"),
        ]
        for col, (label, val) in zip([ec1, ec2, ec3, ec4], examples):
            if col.button(label, key=f"ex_{label}", use_container_width=True):
                st.session_state.research_query = val
                st.rerun()

    if research_btn and vehicle_query.strip():
        with st.status("Running AI agents...", expanded=True) as status:
            st.write("Fetching web sources (Tavily)...")
            t0 = time.time()
            try:
                st.write("Researcher agent synthesizing specs...")
                out = run_automotive_crew(VehicleQuery(query=vehicle_query.strip()))
                st.write("Writer agent formatting report...")
                elapsed = round(time.time() - t0, 1)
                status.update(label=f"Done in {elapsed}s", state="complete")
            except Exception as e:
                status.update(label="Error", state="error")
                st.error(f"Something went wrong: {e}")
                st.stop()

        origin = (out.meta or {}).get("source_origin", "web")
        conf   = out.brief.confidence
        n_src  = len(out.citations)
        badge_conf = "badge-green" if conf == "high" else "badge-amber" if conf == "medium" else "badge-blue"

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-card"><div class="label">Time taken</div><div class="value">{elapsed}s</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><div class="label">Sources</div><div class="value">{n_src}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><div class="label">Confidence</div><div class="value"><span class="badge {badge_conf}">{conf}</span></div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-card"><div class="label">Data source</div><div class="value"><span class="badge badge-purple">{origin}</span></div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        rep_tab, src_tab, debug_tab = st.tabs(["📄 Report", "🔗 Sources", "🧠 Debug"])

        with rep_tab:
            # Convert markdown tables to HTML so Streamlit renders them correctly
            rendered_report = _md_table_to_html(out.markdown_report)
            st.markdown(rendered_report, unsafe_allow_html=True)
            st.download_button(
                "⬇️ Download Report (Markdown)",
                data=out.markdown_report.encode("utf-8"),
                file_name=f"{vehicle_query.strip().replace(' ', '_')}_report.md",
                mime="text/markdown",
            )

        with src_tab:
            if out.citations:
                for i, s in enumerate(out.citations, 1):
                    with st.expander(f"{i}. {s.title or s.url}"):
                        st.markdown(f"**URL:** [{s.url}]({s.url})")
                        if s.snippet:
                            st.caption(s.snippet)
            else:
                st.info("No sources available.")

        with debug_tab:
            st.json(out.brief.model_dump())

    elif research_btn:
        st.warning("Please enter a vehicle name.")
