#!/usr/bin/env bash
# TODO: Upload address DB and PBF artifacts to S3.
#
# This is a stub for future S3 migration from static.osmosis.page.
# Until then, use .tools/upload_static_osmosis_page.sh.
#
# Usage (future):
#   ./upload_s3.sh [DB_FILE] [PBF_FILE]
#
# Required env vars (future):
#   AWS_ACCESS_KEY_ID
#   AWS_SECRET_ACCESS_KEY
#   AWS_REGION
#   S3_BUCKET

set -euo pipefail

# TODO: implement S3 upload
# S3_BUCKET="${S3_BUCKET:-your-bucket-name}"
# DB_FILE="${1:-DE-addresses.osm.db}"
# PBF_FILE="${2:-DE-addresses.osm.pbf}"
#
# aws s3 cp "$DB_FILE" "s3://$S3_BUCKET/osm/$DB_FILE" --acl public-read
# aws s3 cp "${DB_FILE}.md5" "s3://$S3_BUCKET/osm/${DB_FILE}.md5" --acl public-read
# aws s3 cp "$PBF_FILE" "s3://$S3_BUCKET/osm/$PBF_FILE" --acl public-read
# aws s3 cp "${PBF_FILE}.md5" "s3://$S3_BUCKET/osm/${PBF_FILE}.md5" --acl public-read

echo "S3 upload not yet implemented. Use .tools/upload_static_osmosis_page.sh instead." >&2
exit 1
