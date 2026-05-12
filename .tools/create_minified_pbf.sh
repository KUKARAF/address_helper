#!/usr/bin/env bash
#
# Create a minified PBF file containing only address-relevant OSM data.
#
# Usage:
#   .tools/create_minified_pbf.sh DE output.osm.pbf
#   .tools/create_minified_pbf.sh DE staticfiles/DE-addresses.osm.pbf
#
# Arguments:
#   $1 - Country code (e.g., DE, AT, FR) - must exist in links.toml
#   $2 - Output file path for the minified PBF
#
# Requirements:
#   Option 1 (Docker - Recommended):
#     - docker and docker-compose
#   Option 2 (Local):
#     - osmium-tool (https://osmcode.org/osmium-tool/)
#     - curl or wget
#     - Python 3 with tomllib (3.11+) or tomli package
#
# The script will automatically use Docker if available, otherwise fall back to local tools.
# To force local tools: export USE_DOCKER=false

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LINKS_TOML="$PROJECT_ROOT/links.toml"
CACHE_DIR="${PROJECT_ROOT}/.osm-cache"

# Determine whether to use Docker
USE_DOCKER="${USE_DOCKER:-true}"
DOCKER_AVAILABLE=false
if [[ "$USE_DOCKER" == "true" ]] && command -v docker &> /dev/null; then
    DOCKER_AVAILABLE=true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
    exit 1
}

info() {
    echo -e "${GREEN}INFO:${NC} $1"
}

warn() {
    echo -e "${YELLOW}WARN:${NC} $1"
}

# Docker execution wrapper
run_in_docker() {
    local cmd="$1"
    local silent="${2:-false}"
    
    if [[ "$silent" != "true" ]]; then
        info "Running in Docker container..."
    fi
    
    docker run --rm -v "$PROJECT_ROOT:/workspace" -w /workspace address-helper:osm-minifier bash -c "$cmd"
    return $?
}

# Check arguments
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <COUNTRY_CODE> <OUTPUT_FILE>"
    echo "Example: $0 DE staticfiles/DE-addresses.osm.pbf"
    exit 1
fi

COUNTRY_CODE="$1"
OUTPUT_FILE="$2"

# Validate country code format (2 uppercase letters)
if [[ ! "$COUNTRY_CODE" =~ ^[A-Z]{2}$ ]]; then
    error "Country code must be 2 uppercase letters (e.g., DE, AT, FR)"
fi

# Check for required tools
if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
    info "Using Docker for minification"
    
    # Check if Docker image exists, if not build it
    if ! docker image inspect address-helper:osm-minifier &> /dev/null; then
        info "Building Docker image (this may take a minute)..."
        docker build -t address-helper:osm-minifier "$SCRIPT_DIR" || error "Failed to build Docker image"
    fi
else
    warn "Docker not available, using local tools"
    
    if ! command -v osmium &> /dev/null; then
        error "osmium-tool is required but not installed. Either:"
        echo "  1. Install Docker: docker and docker-compose will be used automatically"
        echo "  2. Install osmium-tool locally: apt install osmium-tool"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
        error "curl or wget is required but neither is installed"
    fi
fi

# Check links.toml exists
if [[ ! -f "$LINKS_TOML" ]]; then
    error "links.toml not found at $LINKS_TOML"
fi

# Extract source_url from links.toml using Python
info "Reading source URL for $COUNTRY_CODE from links.toml..."

# Extract source URL from links.toml
if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
    SOURCE_URL=$(run_in_docker "python3 << 'PYEOF'
import sys
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print('ERROR: Python 3.11+ or tomli package required', file=sys.stderr)
        sys.exit(1)

with open('/workspace/links.toml', 'rb') as f:
    config = tomllib.load(f)

countries = config.get('countries', {})
country = countries.get('$COUNTRY_CODE')

if not country:
    print(f'ERROR: Country code $COUNTRY_CODE not found in links.toml', file=sys.stderr)
    sys.exit(1)

source_url = country.get('source_url', '')
if not source_url:
    print(f'ERROR: No source_url defined for $COUNTRY_CODE in links.toml', file=sys.stderr)
    sys.exit(1)

print(source_url)
PYEOF" true)
else
    SOURCE_URL=$(python3 << PYEOF
import sys
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print('ERROR: Python 3.11+ or tomli package required', file=sys.stderr)
        sys.exit(1)

with open('$LINKS_TOML', 'rb') as f:
    config = tomllib.load(f)

countries = config.get('countries', {})
country = countries.get('$COUNTRY_CODE')

if not country:
    print(f'ERROR: Country code $COUNTRY_CODE not found in links.toml', file=sys.stderr)
    sys.exit(1)

source_url = country.get('source_url', '')
if not source_url:
    print(f'ERROR: No source_url defined for $COUNTRY_CODE in links.toml', file=sys.stderr)
    sys.exit(1)

print(source_url)
PYEOF
)
fi

if [[ $? -ne 0 ]] || [[ -z "$SOURCE_URL" ]]; then
    error "Failed to extract source_url for $COUNTRY_CODE from links.toml"
fi

info "Source URL: $SOURCE_URL"

# Create output directory if needed
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
if [[ -n "$OUTPUT_DIR" ]] && [[ "$OUTPUT_DIR" != "." ]]; then
    mkdir -p "$OUTPUT_DIR"
fi

# Use Docker for the entire minification process
if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
    info "Using Docker to download and minify PBF..."
    
    # Ensure cache directory exists
    mkdir -p "$CACHE_DIR"
    
    # Create a cached filename based on the URL
    # Use the last part of the URL (filename) as the cache key
    CACHED_FILENAME=$(basename "$SOURCE_URL")
    CACHED_PBF="$CACHE_DIR/$CACHED_FILENAME"
    
    # Create a temporary script to run in Docker
    DOCKER_SCRIPT=$(mktemp)
    cat > "$DOCKER_SCRIPT" << 'DOCKER_SCRIPT_EOF'
#!/bin/bash
set -o pipefail
SOURCE_URL="$1"
OUTPUT_FILE="$2"
CACHED_PBF="$3"

OUTPUT_ABS="/workspace/$OUTPUT_FILE"

# Create output directory if needed
OUTPUT_DIR=$(dirname "$OUTPUT_ABS")
if [[ -n "$OUTPUT_DIR" ]] && [[ "$OUTPUT_DIR" != "." ]]; then
    mkdir -p "$OUTPUT_DIR"
fi

# Check if we have a cached version
if [[ -f "$CACHED_PBF" ]] && [[ -s "$CACHED_PBF" ]]; then
    echo "Using cached PBF: $CACHED_PBF"
    DOWNLOADED_PBF="$CACHED_PBF"
    FULL_SIZE=$(du -h "$DOWNLOADED_PBF" | cut -f1)
    echo "Cached full PBF: $FULL_SIZE"
else
    # Download the full PBF
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT
    
    DOWNLOADED_PBF="$TEMP_DIR/full.osm.pbf"
    
    echo "Downloading full PBF from Geofabrik (this may take a while)..."
    curl -L --progress-bar -o "$DOWNLOADED_PBF" "$SOURCE_URL" || { echo "Download failed"; exit 1; }
    
    # Verify download
    if [[ ! -s "$DOWNLOADED_PBF" ]]; then
        echo "Downloaded file is empty or missing"
        exit 1
    fi
    
    FULL_SIZE=$(du -h "$DOWNLOADED_PBF" | cut -f1)
    echo "Downloaded full PBF: $FULL_SIZE"
    
    # Cache the downloaded file
    echo "Caching downloaded PBF..."
    mkdir -p "$(dirname "$CACHED_PBF")"
    cp "$DOWNLOADED_PBF" "$CACHED_PBF" || echo "Warning: Failed to cache PBF file"
fi

# Run osmium tags-filter to create minified PBF
echo "Minifying PBF with osmium tags-filter..."
osmium tags-filter "$DOWNLOADED_PBF" \
    "addr:*" \
    "place=city,town,village,suburb,neighbourhood,hamlet,locality" \
    "boundary=administrative,postal_code" \
    "postal_code" \
    "name" \
    "admin_level" \
    -o "$OUTPUT_ABS" \
    --overwrite \
    || { echo "osmium tags-filter failed"; exit 1; }

# Verify output
if [[ ! -s "$OUTPUT_ABS" ]]; then
    echo "Output file is empty or missing"
    exit 1
fi

MINIFIED_SIZE=$(du -h "$OUTPUT_ABS" | cut -f1)
echo "Created minified PBF: $OUTPUT_ABS ($MINIFIED_SIZE)"

# Generate MD5 checksum
MD5_FILE="$OUTPUT_ABS.md5"
md5sum "$OUTPUT_ABS" | awk '{print $1}' > "$MD5_FILE"
echo "Created MD5 checksum: $MD5_FILE"
DOCKER_SCRIPT_EOF
    
    # Run the script inside Docker (mount cache directory too)
    docker run --rm -v "$PROJECT_ROOT:/workspace" -v "$CACHE_DIR:/cache" -v "$DOCKER_SCRIPT:/tmp/minify.sh" -w /workspace \
        address-helper:osm-minifier bash /tmp/minify.sh "$SOURCE_URL" "$OUTPUT_FILE" "/cache/$CACHED_FILENAME" \
        || error "Docker minification failed"
    
    rm -f "$DOCKER_SCRIPT"
    
    MINIFIED_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    info "Created minified PBF: $OUTPUT_FILE ($MINIFIED_SIZE)"
    
    MD5_FILE="${OUTPUT_FILE}.md5"
    
else
    # Local execution
    # Ensure cache directory exists
    mkdir -p "$CACHE_DIR"
    
    # Create a cached filename based on the URL
    CACHED_FILENAME=$(basename "$SOURCE_URL")
    CACHED_PBF="$CACHE_DIR/$CACHED_FILENAME"
    
    # Check if we have a cached version
    if [[ -f "$CACHED_PBF" ]] && [[ -s "$CACHED_PBF" ]]; then
        info "Using cached PBF: $CACHED_PBF"
        DOWNLOADED_PBF="$CACHED_PBF"
        FULL_SIZE=$(du -h "$DOWNLOADED_PBF" | cut -f1)
        info "Cached full PBF: $FULL_SIZE"
    else
        TEMP_DIR=$(mktemp -d)
        trap "rm -rf $TEMP_DIR" EXIT

        DOWNLOADED_PBF="$TEMP_DIR/full.osm.pbf"

        # Download the full PBF
        info "Downloading full PBF from Geofabrik (this may take a while)..."

        if command -v curl &> /dev/null; then
            curl -L --progress-bar -o "$DOWNLOADED_PBF" "$SOURCE_URL" || error "Download failed"
        else
            wget --progress=bar:force -O "$DOWNLOADED_PBF" "$SOURCE_URL" || error "Download failed"
        fi

        # Verify download
        if [[ ! -s "$DOWNLOADED_PBF" ]]; then
            error "Downloaded file is empty or missing"
        fi

        FULL_SIZE=$(du -h "$DOWNLOADED_PBF" | cut -f1)
        info "Downloaded full PBF: $FULL_SIZE"
        
        # Cache the downloaded file
        info "Caching downloaded PBF..."
        cp "$DOWNLOADED_PBF" "$CACHED_PBF" || warn "Failed to cache PBF file"
    fi

    # Run osmium tags-filter to create minified PBF
    # Keep only address-relevant tags (see osm-filter-spec.md)
    info "Minifying PBF with osmium tags-filter..."

    osmium tags-filter "$DOWNLOADED_PBF" \
        "addr:*" \
        "place=city,town,village,suburb,neighbourhood,hamlet,locality" \
        "boundary=administrative,postal_code" \
        "postal_code" \
        "name" \
        "admin_level" \
        -o "$OUTPUT_FILE" \
        --overwrite \
        || error "osmium tags-filter failed"

    # Verify output
    if [[ ! -s "$OUTPUT_FILE" ]]; then
        error "Output file is empty or missing"
    fi

    MINIFIED_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    info "Created minified PBF: $OUTPUT_FILE ($MINIFIED_SIZE)"

    # Generate MD5 checksum
    MD5_FILE="${OUTPUT_FILE}.md5"
    if command -v md5sum &> /dev/null; then
        md5sum "$OUTPUT_FILE" | awk '{print $1}' > "$MD5_FILE"
    elif command -v md5 &> /dev/null; then
        md5 -q "$OUTPUT_FILE" > "$MD5_FILE"
    else
        warn "Neither md5sum nor md5 found, skipping checksum generation"
        MD5_FILE=""
    fi
fi

if [[ -n "$MD5_FILE" ]] && [[ -f "$MD5_FILE" ]]; then
    info "Created MD5 checksum: $MD5_FILE"
fi

# Summary
echo ""
echo "=========================================="
echo "Minification complete!"
echo "=========================================="
echo "Country:      $COUNTRY_CODE"
echo "Full PBF:     $FULL_SIZE"
echo "Minified PBF: $MINIFIED_SIZE"
echo "Output:       $OUTPUT_FILE"
if [[ -n "$MD5_FILE" ]]; then
    echo "Checksum:     $MD5_FILE"
fi
echo ""
echo "Next steps:"
echo "  1. Upload $OUTPUT_FILE to static.osmosis.page/osm/"
echo "  2. Upload $MD5_FILE to static.osmosis.page/osm/"
echo "  3. Update links.toml pbf_url and checksum_url for $COUNTRY_CODE"
