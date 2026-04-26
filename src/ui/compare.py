from __future__ import annotations
import time
import streamlit as st
from src.workflow import run_comparison


def render_compare_tab() -> None:
    st.markdown("### Compare two cars side by side")
    st.caption("Both cars are researched in parallel by AI agents, then compared across key specs.")

    with st.container(border=True):
        col_a, col_vs, col_b = st.columns([5, 1, 5])
        with col_a:
            car_a = st.text_input(
                "Car A",
                placeholder="e.g. Hyundai Creta 2024",
                key="compare_a",
            )
        with col_vs:
            st.markdown("<br><br><div style='text-align:center;font-weight:600;font-size:1.1rem;color:#6b7280'>VS</div>", unsafe_allow_html=True)
        with col_b:
            car_b = st.text_input(
                "Car B",
                placeholder="e.g. Kia Seltos 2024",
                key="compare_b",
            )

        st.caption("Popular comparisons:")
        cc1, cc2, cc3 = st.columns(3)
        comp_examples = [
            ("Creta vs Seltos", "Hyundai Creta 2024", "Kia Seltos 2024"),
            ("Nexon EV vs MG ZS EV", "Tata Nexon EV 2024", "MG ZS EV 2024"),
            ("BMW M4 vs AMG C63", "BMW M4 Competition 2024", "Mercedes AMG C63 2024"),
        ]
        for col, (label, va, vb) in zip([cc1, cc2, cc3], comp_examples):
            if col.button(label, key=f"cc_{label}", use_container_width=True):
                st.session_state.compare_a = va
                st.session_state.compare_b = vb
                st.rerun()

        compare_btn = st.button("Compare Cars", type="primary", use_container_width=True)

    if compare_btn and car_a.strip() and car_b.strip():
        with st.status("Researching both cars in parallel...", expanded=True) as status:
            st.write(f"Agent A → {car_a}")
            st.write(f"Agent B → {car_b}")
            t0 = time.time()
            try:
                out_a, out_b = run_comparison(car_a.strip(), car_b.strip())
                elapsed = round(time.time() - t0, 1)
                status.update(label=f"Both researched in {elapsed}s", state="complete")
            except Exception as e:
                status.update(label="Error", state="error")
                st.error(f"Comparison failed: {e}")
                st.stop()

        st.success(f"Comparison completed in {elapsed}s (parallel)")
        st.markdown("<br>", unsafe_allow_html=True)

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(f'<div class="compare-col">', unsafe_allow_html=True)
            st.markdown(f"#### {car_a}")
            _conf_a = out_a.brief.confidence
            st.markdown(f'<span class="badge badge-{"green" if _conf_a=="high" else "amber"}">{_conf_a} confidence</span>', unsafe_allow_html=True)
            st.markdown(out_a.markdown_report)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_r:
            st.markdown(f'<div class="compare-col">', unsafe_allow_html=True)
            st.markdown(f"#### {car_b}")
            _conf_b = out_b.brief.confidence
            st.markdown(f'<span class="badge badge-{"green" if _conf_b=="high" else "amber"}">{_conf_b} confidence</span>', unsafe_allow_html=True)
            st.markdown(out_b.markdown_report)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Quick Spec Comparison")
        brief_a = out_a.brief
        brief_b = out_b.brief

        spec_rows = [
            ("Engine",       brief_a.engine,      brief_b.engine),
            ("Power",        brief_a.power,        brief_b.power),
            ("Torque",       brief_a.torque,       brief_b.torque),
            ("Transmission", brief_a.transmission, brief_b.transmission),
            ("Drivetrain",   brief_a.drivetrain,   brief_b.drivetrain),
            ("Fuel Economy", brief_a.fuel_economy, brief_b.fuel_economy),
            ("Weight",       brief_a.weight,       brief_b.weight),
            ("Pricing",      brief_a.pricing,      brief_b.pricing),
            ("Safety",       brief_a.safety,       brief_b.safety),
        ]

        tbl_header = f"| Spec | {car_a} | {car_b} |\n|------|------|------|\n"
        tbl_rows = "".join(
            f"| **{spec}** | {str(va or 'N/A')} | {str(vb or 'N/A')} |\n"
            for spec, va, vb in spec_rows
        )
        st.markdown(tbl_header + tbl_rows)

        dl1, dl2 = st.columns(2)
        dl1.download_button(
            f"⬇️ Download {car_a} Report",
            data=out_a.markdown_report.encode(),
            file_name=f"{car_a.replace(' ', '_')}_report.md",
        )
        dl2.download_button(
            f"⬇️ Download {car_b} Report",
            data=out_b.markdown_report.encode(),
            file_name=f"{car_b.replace(' ', '_')}_report.md",
        )

    elif compare_btn:
        st.warning("Please enter both car names.")
