FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# HOME=/app ensures ONNXMiniLM_L6_V2 (which hardcodes Path.home()/.cache/chroma)
# writes to /app/.cache/chroma — which is mounted as a persistent volume.
ENV HOME=/app
ENV CHROMA_CACHE_DIR=/app/.chroma_cache

RUN mkdir -p data/generated_images && mkdir -p .chroma

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
