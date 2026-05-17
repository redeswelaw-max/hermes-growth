FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install tini (process supervisor) and pip (for Postiz Lite deps).  Node.js is
# NOT needed because frontends are pre-built locally and committed.
RUN apt-get update && \
    apt-get install -y --no-install-recommends tini gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/hermes

# Copy the full repo (Hermes source + pre-built assets + Postiz Lite)
COPY . .

# Create virtualenv and install Hermes Python dependencies using the committed
# uv.lock.  --frozen skips resolution (very fast, reproducible).
RUN uv venv .venv && \
    VIRTUAL_ENV=/opt/hermes/.venv uv sync --frozen --extra cli --extra mcp --extra messaging --extra web && \
    VIRTUAL_ENV=/opt/hermes/.venv uv pip install fastapi==0.115.0 uvicorn==0.32.0 python-multipart==0.0.17

ENV PATH="/opt/hermes/.venv/bin:$PATH"
ENV HOME=/data
ENV HERMES_HOME=/data/.hermes
ENV HERMES_TUI_DIR=/opt/hermes/ui-tui
ENV HERMES_ALLOW_ROOT_GATEWAY=1
ENV GATEWAY_ALLOW_ALL_USERS=true
ENV KIMI_API_KEY=sk-kimi-dLLtefCcIELCsaejYCwJD5zd66vNOQhawc1rna5wKm4I5ALI2fYhnasRMlCtfWxC
ENV KIMI_BASE_URL=https://api.moonshot.ai/v1
ENV TELEGRAM_BOT_TOKEN=8603805979:AAH_qWK_eIrBRfX9SnBrveVI4FgH-UHA3fk

# Postiz Lite — self-hosted microservice running inside the same container
ENV POSTIZ_API_KEY=postiz-lite-internal-key
ENV POSTIZ_BASE_URL=http://localhost:5000
ENV PORT=5000
ENV DB_PATH=/data/postiz_lite.db

# Pre-create essential directories so the container starts cleanly.
RUN mkdir -p /data/.hermes/{cron,sessions,logs,hooks,memories,skills,skins,plans,workspace,home} /data/postiz-lite

# Expose Postiz Lite port so Railway assigns a public URL
EXPOSE 5000

# Start Postiz Lite in background, then Hermes gateway in foreground.
# A small shell script is the simplest supervisor for two processes.
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["sh", "-c", "python /opt/hermes/postiz-lite/main.py & exec hermes gateway"]
