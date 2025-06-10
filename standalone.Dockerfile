FROM nikolaik/python-nodejs:python3.12-nodejs22

# Shared environment variables
ENV POETRY_VIRTUALENVS_PATH=/openhands/poetry \
    MAMBA_ROOT_PREFIX=/openhands/micromamba \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    EDITOR=code \
    VISUAL=code \
    GIT_EDITOR="code --wait" \
    OPENVSCODE_SERVER_ROOT=/openhands/.openvscode-server


RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# Install base system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget curl ca-certificates sudo apt-utils git jq tmux build-essential ripgrep \
        #{%- if 'ubuntu' in base_image and (base_image.endswith(':latest') or base_image.endswith(':24.04')) -%}
        libgl1 \
        #{%- else %}
        libgl1-mesa-glx \
        #{% endif -%}
        libasound2-plugins libatomic1  \
        # Common utilities that may be needed by GUI or other extensions
        imagemagick \
        net-tools \
        unzip && \
        apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    # {%- if 'ubuntu' in base_image -%}
    # curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    # TZ=Etc/UTC DEBIAN_FRONTEND=noninteractive \
    #     apt-get install -y --no-install-recommends nodejs python3.12 python-is-python3 python3-pip python3.12-venv && \
    # corepack enable yarn && \
    # {% endif -%}


# {% if 'ubuntu' in base_image %}
# RUN ln -s "$(dirname $(which node))/corepack" /usr/local/bin/corepack && \
#     npm install -g corepack && corepack enable yarn && \
#     curl -fsSL --compressed https://install.python-poetry.org | python -
# {% endif %}

# Install uv (required by MCP)
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/openhands/bin" sh
# Add /openhands/bin to PATH
ENV PATH="/openhands/bin:${PATH}"

# Remove UID 1000 named pn or ubuntu, so the 'openhands' user can be created from ubuntu hosts
RUN (if getent passwd 1000 | grep -q pn; then userdel pn; fi) && \
    (if getent passwd 1000 | grep -q ubuntu; then userdel ubuntu; fi)


# Create necessary directories
RUN mkdir -p /openhands && \
    mkdir -p /openhands/logs && \
    mkdir -p /openhands/poetry

# ================================================================
# GUI Extensions Configuration
# ================================================================
# Install GUI dependencies and desktop environment

# Set GUI environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_PRIORITY=high

# Optional: Modify apt sources to use faster mirrors (uncomment if needed)
# RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources
# RUN sed -i 's/deb.debian.org/ftp.jaist.ac.jp/g' /etc/apt/sources.list.d/debian.sources

# Install GUI and desktop environment packages
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y --no-install-recommends install \
    # UI Requirements
    xvfb \
    tint2 \
    xterm \
    xdotool \
    scrot \
    mutter \
    x11vnc \
    openbox \
    supervisor \
    novnc \
    websockify \
    xdg-utils \
    python3-xdg \
    x11-xserver-utils \
    netcat-traditional \
    chromium \
    # 最小键盘支持包
    keyboard-configuration \
    xkb-data \
    console-setup \
    locales \
    # Desktop applications
    libreoffice \
    x11-apps \
    xpdf \
    gedit \
    xpaint \
    galculator \
    pcmanfm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install noVNC
RUN rm -rf /opt/noVNC && rm -rf /opt/websockify
RUN git clone --depth 1 --branch v1.5.0 https://github.com/novnc/noVNC.git /opt/noVNC && \
    git clone --depth 1 --branch v0.12.0 https://github.com/novnc/websockify /opt/noVNC/utils/websockify && \
    ln -s /opt/noVNC/vnc.html /opt/noVNC/index.html
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=en_US.UTF-8
# Setup GUI user environment (use openhands user if available, otherwise create new)
ENV GUI_USERNAME=openhands
ENV GUI_HOME=/home/$GUI_USERNAME
# Create GUI user only if it doesn't exist, otherwise use existing openhands user
RUN echo "Checking if user $GUI_USERNAME exists..." && \
    if getent passwd "$GUI_USERNAME" > /dev/null 2>&1; then \
        echo "User $GUI_USERNAME already exists, using existing user"; \
        echo "User info: $(id $GUI_USERNAME)"; \
    else \
        echo "User $GUI_USERNAME does not exist, creating new user"; \
        useradd -m -s /bin/bash -d $GUI_HOME $GUI_USERNAME && \
        echo "${GUI_USERNAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
        echo "User $GUI_USERNAME created successfully"; \
    fi

# Set display configuration variables
ARG DISPLAY_NUM=1
ARG HEIGHT=768
ARG WIDTH=1024
ENV DISPLAY_NUM=$DISPLAY_NUM
ENV HEIGHT=$HEIGHT
ENV WIDTH=$WIDTH


# Set ownership for GUI user
RUN chown -R $GUI_USERNAME:$GUI_USERNAME $GUI_HOME

# Reference:
# 1. https://github.com/gitpod-io/openvscode-server
# 2. https://github.com/gitpod-io/openvscode-releases

# Setup VSCode Server
ARG RELEASE_TAG="openvscode-server-v1.98.2"
ARG RELEASE_ORG="gitpod-io"
# ARG USERNAME=openvscode-server
# ARG USER_UID=1000
# ARG USER_GID=1000

RUN if [ -z "${RELEASE_TAG}" ]; then \
        echo "The RELEASE_TAG build arg must be set." >&2 && \
        exit 1; \
    fi && \
    arch=$(uname -m) && \
    if [ "${arch}" = "x86_64" ]; then \
        arch="x64"; \
    elif [ "${arch}" = "aarch64" ]; then \
        arch="arm64"; \
    elif [ "${arch}" = "armv7l" ]; then \
        arch="armhf"; \
    fi && \
    wget https://github.com/${RELEASE_ORG}/openvscode-server/releases/download/${RELEASE_TAG}/${RELEASE_TAG}-linux-${arch}.tar.gz && \
    tar -xzf ${RELEASE_TAG}-linux-${arch}.tar.gz && \
    if [ -d "${OPENVSCODE_SERVER_ROOT}" ]; then rm -rf "${OPENVSCODE_SERVER_ROOT}"; fi && \
    mv ${RELEASE_TAG}-linux-${arch} ${OPENVSCODE_SERVER_ROOT} && \
    cp ${OPENVSCODE_SERVER_ROOT}/bin/remote-cli/openvscode-server ${OPENVSCODE_SERVER_ROOT}/bin/remote-cli/code && \
    rm -f ${RELEASE_TAG}-linux-${arch}.tar.gz



# ================================================================
# START: Build Runtime Image from Scratch
# ================================================================
# This is used in cases where the base image is something more generic like nikolaik/python-nodejs
# rather than the current OpenHands release


# Install micromamba
RUN mkdir -p /openhands/micromamba/bin && \
    /bin/bash -c "PREFIX_LOCATION=/openhands/micromamba BIN_FOLDER=/openhands/micromamba/bin INIT_YES=no CONDA_FORGE_YES=yes $(curl -L https://micro.mamba.pm/install.sh)" && \
    /openhands/micromamba/bin/micromamba config remove channels defaults && \
    /openhands/micromamba/bin/micromamba config list

# ================================================================
# END: Build Runtime Image from Scratch
# ================================================================
