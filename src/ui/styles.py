from __future__ import annotations
import streamlit as st


def inject_styles() -> None:
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
        padding: 2.5rem 2rem 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 { font-size: 2.6rem; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
    .main-header p  { font-size: 1.05rem; opacity: 0.8; margin: 0.5rem 0 0; }

    .metric-card {
        background: white;
        border: 1px solid #e8eaed;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }
    .metric-card .label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-card .value { font-size: 1.5rem; font-weight: 600; color: #111827; margin-top: 4px; }

    .section-card {
        background: white;
        border: 1px solid #e8eaed;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .badge-green  { background: #d1fae5; color: #065f46; }
    .badge-blue   { background: #dbeafe; color: #1e40af; }
    .badge-amber  { background: #fef3c7; color: #92400e; }
    .badge-purple { background: #ede9fe; color: #5b21b6; }

    .compare-col {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] { background: #302b63 !important; color: white !important; }

    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-1px); }

    div[data-testid="stExpander"] { border: 1px solid #e8eaed; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)


def render_header() -> None:
    st.markdown("""
<div class="main-header">
    <h1>🚗 AutoVerse AI</h1>
    <p>Agentic research · Generative design concepts · Side-by-side comparison</p>
</div>
""", unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown("---")
    st.markdown(
        '<p style="text-align:center;color:#9ca3af;font-size:0.8rem;">'
        'AutoVerse AI · Agentic AI + Generative AI · Powered by CrewAI, Groq, Tavily, ChromaDB'
        '</p>',
        unsafe_allow_html=True,
    )
