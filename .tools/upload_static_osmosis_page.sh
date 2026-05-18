#!/usr/bin/env bash
# Upload address DB and PBF artifacts to static.osmosis.page (rafa@bigboy).
#
# Usage:
#   ./upload_static_osmosis_page.sh [DB_FILE] [PBF_FILE]
#
# Defaults:
#   DB_FILE  = DE-addresses.osm.db   (in current directory)
#   PBF_FILE = DE-addresses.osm.pbf  (in current directory)
#
# After upload, update db_checksum in address_standardizer/data/links.toml.

set -euo pipefail

REMOTE_HOST="rafa@bigboy"
REMOTE_DIR="/home/rafa/env/static/public/osm"

DB_FILE="${1:-DE-addresses.osm.db}"
PBF_FILE="${2:-DE-addresses.osm.pbf}"

if [[ ! -f "$DB_FILE" ]]; then
    echo "ERROR: DB file not found: $DB_FILE" >&2
    exit 1
fi

# Generate MD5 sidecar files
md5sum "$DB_FILE" | awk '{print $1}' > "${DB_FILE}.md5"
echo "DB  MD5: $(cat "${DB_FILE}.md5")"

if [[ -f "$PBF_FILE" ]]; then
    md5sum "$PBF_FILE" | awk '{print $1}' > "${PBF_FILE}.md5"
    echo "PBF MD5: $(cat "${PBF_FILE}.md5")"
fi

# Upload DB + MD5
echo "Uploading $DB_FILE to $REMOTE_HOST:$REMOTE_DIR ..."
rsync -avz --progress \
    "$DB_FILE" "${DB_FILE}.md5" \
    "$REMOTE_HOST:$REMOTE_DIR/"

# Upload PBF + MD5 if available
if [[ -f "$PBF_FILE" ]]; then
    echo "Uploading $PBF_FILE to $REMOTE_HOST:$REMOTE_DIR ..."
    rsync -avz --progress \
        "$PBF_FILE" "${PBF_FILE}.md5" \
        "$REMOTE_HOST:$REMOTE_DIR/"
fi

echo ""
echo "Done. Update db_checksum in address_standardizer/data/links.toml:"
echo "  db_checksum = \"$(cat "${DB_FILE}.md5")\""
