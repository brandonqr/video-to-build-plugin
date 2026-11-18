FROM node:22-bookworm-slim AS node_base
FROM ghcr.io/astral-sh/uv:latest AS uv_bin

FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    UV_TOOL_BIN_DIR=/usr/local/bin \
    UV_TOOL_DIR=/opt/uv-tools \
    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

# Copy Node.js 22 and uv
COPY --from=node_base /usr/local /usr/local
COPY --from=uv_bin /uv /uvx /usr/local/bin/

# System tools: ffmpeg, headless Blender, Xvfb + OpenGL/Mesa for WebGL QA
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    ffmpeg \
    blender \
    xvfb \
    libatomic1 \
    libgl1 \
    libgl1-mesa-dri \
    libegl1 \
    libgles2 \
    && rm -rf /var/lib/apt/lists/*

# Python CLI tools: yt-dlp + HKUDS CLI-Anything hub + Playwright (Chromium for WebGL QA)
RUN uv tool install yt-dlp \
    && uv tool install cli-anything-hub \
    && pip install --no-cache-dir playwright \
    && playwright install --with-deps chromium \
    && rm -rf /root/.cache

# Higgsfield official CLI
RUN npm install -g @higgsfield/cli && npm cache clean --force

# Copy the reusable Antigravity plugin
WORKDIR /opt/video-to-build-plugin
COPY . /opt/video-to-build-plugin

WORKDIR /workspace

CMD ["bash"]
