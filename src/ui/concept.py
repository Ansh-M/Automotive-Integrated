from __future__ import annotations
import time
import streamlit as st
from src.concept_engine import get_concept_engine


def render_concept_tab() -> None:
    st.markdown("### Generate an automotive design concept")
    st.caption("Enter any concept — the AI generates a detailed design narrative and an optimized image generation prompt.")

    if "_pending_concept" in st.session_state:
        st.session_state.concept_input = st.session_state.pop("_pending_concept")

    with st.container(border=True):
        concept_input = st.text_area(
            "Your concept",
            placeholder=(
                "e.g. A rugged yet futuristic electric SUV designed for Indian highways, "
                "inspired by Indian heritage motifs with a bold stance and sustainable materials..."
            ),
            height=100,
            label_visibility="collapsed",
            key="concept_input",
        )

        st.caption("Need inspiration?")
        ic1, ic2, ic3 = st.columns(3)
        concept_examples = [
            ("Electric SUV India", "A powerful electric SUV built for Indian roads, blending heritage design with futuristic technology"),
            ("Luxury Supercar", "A hypercar combining Italian styling with German engineering, targeting the ultra-luxury segment"),
            ("Autonomous City Car", "A compact autonomous vehicle for smart cities, focused on shared mobility and zero emissions"),
        ]
        for col, (label, val) in zip([ic1, ic2, ic3], concept_examples):
            if col.button(label, key=f"ci_{label}", use_container_width=True):
                st.session_state._pending_concept = val
                st.rerun()

        concept_btn = st.button("Generate Concept", type="primary", use_container_width=True)

    if concept_btn and concept_input.strip():
        with st.spinner("Generating design narrative and image prompt..."):
            t0 = time.time()
            try:
                engine = get_concept_engine()
                result = engine.generate_concept(concept_input.strip())
                elapsed = round(time.time() - t0, 1)
            except Exception as e:
                st.error(f"Generation failed: {e}")
                st.stop()

        st.success(f"Concept generated in {elapsed}s")

        col_narr, col_img = st.columns([3, 2])

        with col_narr:
            st.markdown("#### Design Narrative")
            st.markdown(result.narrative)

        with col_img:
            st.markdown("#### Image Generation Prompt")
            st.markdown(
                '<p style="font-size:0.8rem;color:#6b7280;">Copy this prompt into DALL-E, Midjourney, or Stable Diffusion:</p>',
                unsafe_allow_html=True,
            )
            st.code(result.image_prompt, language=None)
            st.download_button(
                "⬇️ Copy Image Prompt",
                data=result.image_prompt,
                file_name="image_prompt.txt",
                mime="text/plain",
            )

        with st.expander("Full details (JSON)"):
            st.json({
                "user_prompt": result.user_prompt,
                "narrative": result.narrative,
                "image_prompt": result.image_prompt,
                "processing_time_s": result.processing_time,
            })

    elif concept_btn:
        st.warning("Please enter a concept prompt.")
