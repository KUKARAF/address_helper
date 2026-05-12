"""
create_street_postcode_city_only_pbf.py

Updates links.toml after a minified PBF has been uploaded to static.osmosis.page.

Called by create_street_postcode_city_only_pbf.sh — not intended for direct use.

Usage:
    python create_street_postcode_city_only_pbf.py \
        --toml links.toml \
        --country DE \
        --minified-url https://static.osmosis.page/osm/DE-addresses-latest.osm.pbf \
        --minified-checksum https://static.osmosis.page/osm/DE-addresses-latest.osm.pbf.md5 \
        --minified-size-mb 210.4 \
        --timestamp 2024-01-15T12:00:00Z
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path


def load_toml(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def dump_toml(data: dict, path: Path) -> None:
    """
    Write data back to a TOML file.

    We write TOML manually rather than using a third-party library (e.g. tomlkit)
    to keep dependencies minimal. The structure of links.toml is simple enough
    that this is maintainable.
    """
    lines: list[str] = []

    # [meta]
    lines.append("# links.toml")
    lines.append("# Auto-managed by CI/CD pipeline. See .tools/ for update scripts.")
    lines.append("")
    lines.append("[meta]")
    meta = data.get("meta", {})
    lines.append(f'schema_version = "{meta.get("schema_version", "1")}"')
    lines.append(f'static_base_url = "{meta.get("static_base_url", "")}"')
    lines.append(f'last_updated = "{meta.get("last_updated", "")}"')
    lines.append("")

    # [countries.*]
    for iso_code, entry in data.get("countries", {}).items():
        lines.append(f"[countries.{iso_code}]")
        lines.append(f'name = "{entry["name"]}"')
        lines.append(f'full = "{entry["full"]}"')
        lines.append(f'full_checksum = "{entry.get("full_checksum", "")}"')
        lines.append(f'minified = "{entry.get("minified", "")}"')
        lines.append(f'minified_checksum = "{entry.get("minified_checksum", "")}"')
        lines.append(f'minified_size_mb = {entry.get("minified_size_mb", 0)}')
        lines.append(f'last_minified = "{entry.get("last_minified", "")}"')
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update links.toml after a minified PBF upload."
    )
    parser.add_argument("--toml",               required=True,  help="Path to links.toml")
    parser.add_argument("--country",            required=True,  help="ISO 3166-1 alpha-2 code, e.g. DE")
    parser.add_argument("--minified-url",       required=True,  help="Public URL of the uploaded minified PBF")
    parser.add_argument("--minified-checksum",  required=True,  help="Public URL of the MD5 checksum file")
    parser.add_argument("--minified-size-mb",   required=True,  type=float, help="File size in MB")
    parser.add_argument("--timestamp",          required=False, help="ISO 8601 timestamp (default: now UTC)")
    args = parser.parse_args()

    toml_path = Path(args.toml)
    if not toml_path.exists():
        print(f"ERROR: links.toml not found at {toml_path}", file=sys.stderr)
        sys.exit(1)

    iso_code = args.country.upper()
    timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    data = load_toml(toml_path)

    if iso_code not in data.get("countries", {}):
        print(f"ERROR: Country '{iso_code}' not found in links.toml", file=sys.stderr)
        sys.exit(1)

    # Update the country entry
    data["countries"][iso_code]["minified"]          = args.minified_url
    data["countries"][iso_code]["minified_checksum"] = args.minified_checksum
    data["countries"][iso_code]["minified_size_mb"]  = args.minified_size_mb
    data["countries"][iso_code]["last_minified"]     = timestamp

    # Update meta timestamp
    data["meta"]["last_updated"] = timestamp

    dump_toml(data, toml_path)
    print(f"Updated links.toml: [{iso_code}] minified → {args.minified_url}")


if __name__ == "__main__":
    main()
