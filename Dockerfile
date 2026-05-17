FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ARG HERMES_REF=v0.14.0

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates git tini && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Clone Hermes Agent official release
RUN git clone --depth 1 --branch ${HERMES_REF} https://github.com/NousResearch/hermes-agent.git /opt/hermes-agent && \
    cd /opt/hermes-agent && \
    uv pip install --system --no-cache -e ".[cron,cli,mcp,web]"

# Pre-build web dashboard
RUN cd /opt/hermes-agent/web && \
    npm install --silent && \
    npm run build

# Pre-build TUI
RUN cd /opt/hermes-agent/ui-tui && \
    npm install --silent --no-fund --no-audit --progress=false && \
    npm run build

# Copy our growth-marketing skills into optional-skills
COPY optional-skills/growth-marketing /opt/hermes-agent/optional-skills/growth-marketing

# Create data directory
RUN mkdir -p /data/.hermes

ENV HOME=/data
ENV HERMES_HOME=/data/.hermes
ENV HERMES_TUI_DIR=/opt/hermes-agent/ui-tui

ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["hermes", "gateway"]
