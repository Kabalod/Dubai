# syntax=docker/dockerfile:1

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Base tooling useful for background agents; do NOT copy project code here
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    openssh-client \
    build-essential \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
    unzip \
    zip \
    sudo \
    jq \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 LTS for JS tooling commonly needed in this repo
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get update && apt-get install -y nodejs \
    && npm i -g pnpm@9 yarn@1.22 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and set home as workdir
RUN useradd -ms /bin/bash ubuntu \
    && echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER ubuntu
WORKDIR /home/ubuntu

ENV PATH="/home/ubuntu/.local/bin:${PATH}"


