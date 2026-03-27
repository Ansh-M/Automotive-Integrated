# Multi-Agent Automotive System (CrewAI + Groq + Tavily + ChromaDB)

This project implements a **collaborative 2-agent automotive workflow**:

- **Researcher Agent**: uses **Tavily web search** to find car specs + sources, and **persists/caches** the retrieved sources in **ChromaDB**.
- **Writer Agent**: consumes the **strict JSON brief** produced by the Researcher and outputs a **clean Markdown report** with citations.

The app is delivered as a **Streamlit** UI.

## Requirements

- Python **3.9+**
- A **Groq API key**
- A **Tavily API key** (Tavily typically offers a free tier for development/testing; create an account and generate a key).

## Setup

1) Create a virtual environment (recommended):

```bash
python -m venv .venv
```

2) Activate it:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

3) Install dependencies:

```bash
pip install -r requirements.txt
```

4) Create your `.env`:

- Copy `.env.example` → `.env`
- Fill in:
  - `GROQ_API_KEY`
  - `TAVILY_API_KEY`

## Run (Streamlit)

```bash
streamlit run streamlit_app.py
```

## How the handoff works

- The **Researcher** task must output **ONLY JSON** (validated by Pydantic).
- The **Writer** task receives that exact JSON via `{research_brief_json}` and outputs **ONLY Markdown**.

## Persistence / caching (ChromaDB)

By default, the ChromaDB persistence directory is:

- `CHROMA_PERSIST_DIR=.chroma`

Re-running the same vehicle queries will reuse cached sources when possible.

