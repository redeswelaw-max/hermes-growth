FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install only tini (process supervisor).  Node.js is NOT needed because
# web dashboard and TUI were pre-built locally and committed.
RUN apt-get update && \
    apt-get install -y --no-install-recommends tini && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/hermes

# Copy the full repo (Hermes source + pre-built web assets + pre-built TUI +
# optional-skills, plugins, etc.)
COPY . .

# Create virtualenv and install Python dependencies using the committed
# uv.lock.  --frozen skips resolution (very fast, reproducible).
RUN uv venv .venv && \
    VIRTUAL_ENV=/opt/hermes/.venv uv sync --frozen --extra cli --extra mcp --extra messaging --extra web

ENV PATH="/opt/hermes/.venv/bin:$PATH"
ENV HOME=/data
ENV HERMES_HOME=/data/.hermes
ENV HERMES_TUI_DIR=/opt/hermes/ui-tui
ENV HERMES_ALLOW_ROOT_GATEWAY=1
ENV GATEWAY_ALLOW_ALL_USERS=true
ENV KIMI_API_KEY=sk-kimi-dLLtefCcIELCsaejYCwJD5zd66vNOQhawc1rna5wKm4I5ALI2fYhnasRMlCtfWxC
ENV KIMI_BASE_URL=https://api.moonshot.ai/v1
ENV TELEGRAM_BOT_TOKEN=8603805979:AAH_qWK_eIrBRfX9SnBrveVI4FgH-UHA3fk
# Postiz social media scheduling (optional — tools are gated on this key)
ENV POSTIZ_API_KEY=""
ENV POSTIZ_BASE_URL=https://api.postiz.com

# Pre-create essential directories so the container starts cleanly.
RUN mkdir -p /data/.hermes/{cron,sessions,logs,hooks,memories,skills,skins,plans,workspace,home}

# Railway injects env vars at runtime; secrets are NOT baked into the image.
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["hermes", "gateway"]
