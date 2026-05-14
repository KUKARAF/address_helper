# Dockerfile for creating minified OSM PBF files
# Contains all dependencies needed for filtering and minifying PBF data

FROM debian:bookworm-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    osmium-tool \
    curl \
    wget \
    python3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]
