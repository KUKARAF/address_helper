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
#   - osmium-tool (https://osmcode.org/osmium-tool/)
#   - curl or wget
#   - Python 3 with tomllib (3.11+) or tomli package

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LINKS_TOML="$PROJECT_ROOT/links.toml"

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
if ! command -v osmium &> /dev/null; then
    error "osmium-tool is required but not installed. Install with: apt install osmium-tool"
fi

if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
    error "curl or wget is required but neither is installed"
fi

# Check links.toml exists
if [[ ! -f "$LINKS_TOML" ]]; then
    error "links.toml not found at $LINKS_TOML"
fi

# Extract source_url from links.toml using Python
info "Reading source URL for $COUNTRY_CODE from links.toml..."

SOURCE_URL=$(python3 << EOF
import sys
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("ERROR: Python 3.11+ or tomli package required", file=sys.stderr)
        sys.exit(1)

with open("$LINKS_TOML", "rb") as f:
    config = tomllib.load(f)

countries = config.get("countries", {})
country = countries.get("$COUNTRY_CODE")

if not country:
    print(f"ERROR: Country code $COUNTRY_CODE not found in links.toml", file=sys.stderr)
    sys.exit(1)

source_url = country.get("source_url", "")
if not source_url:
    print(f"ERROR: No source_url defined for $COUNTRY_CODE in links.toml", file=sys.stderr)
    sys.exit(1)

print(source_url)
EOF
)

if [[ $? -ne 0 ]] || [[ -z "$SOURCE_URL" ]]; then
    error "Failed to extract source_url for $COUNTRY_CODE from links.toml"
fi

info "Source URL: $SOURCE_URL"

# Create temp directory for download
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

# Create output directory if needed
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
if [[ -n "$OUTPUT_DIR" ]] && [[ "$OUTPUT_DIR" != "." ]]; then
    mkdir -p "$OUTPUT_DIR"
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
