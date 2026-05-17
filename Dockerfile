FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install system deps: git, tini, nodejs
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates git tini && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/hermes-agent

# Copy Hermes Agent source (v0.14.0 + our skills)
COPY . /opt/hermes-agent/

# Install hermes-agent with extras (omit mistral due to PyPI quarantine)
RUN uv pip install --system --no-cache -e ".[modal,daytona,vercel,messaging,matrix,cron,cli,dev,tts-premium,slack,pty,honcho,mcp,homeassistant,sms,acp,voice,dingtalk,feishu,google,bedrock,web]"

# Pre-build React dashboard
RUN cd /opt/hermes-agent/web && \
    npm install --silent && \
    npm run build

# Pre-build TUI (keep for runtime Chat tab)
RUN cd /opt/hermes-agent/ui-tui && \
    npm install --silent --no-fund --no-audit --progress=false && \
    npm run build

# Create data directory
RUN mkdir -p /data/.hermes

ENV HOME=/data
ENV HERMES_HOME=/data/.hermes
ENV HERMES_TUI_DIR=/opt/hermes-agent/ui-tui

# Entrypoint: tini -> hermes gateway
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["hermes", "gateway"]
