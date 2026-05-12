# Architecture

## Overview

Two independent flows:

1. **Flow 1 (CI/CD)**: Downloads full PBF → minifies → uploads → updates `links.toml`
2. **Flow 2 (Library)**: Reads `pbf_url` from `links.toml` → downloads minified PBF → queries with pyosmium

Flow 2 is not aware of Flow 1. It only uses the `pbf_url` field in `links.toml`.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Flow 1: CI/CD Pipeline                            │
│                                                                      │
│  links.toml                                                          │
│    │  read source_url                                               │
│    ▼                                                                 │
│  download.geofabrik.de/europe/germany-latest.osm.pbf (~4GB)         │
│    │                                                                 │
│    ▼                                                                 │
│  osmium tags-filter (see osm-filter-spec.md)                        │
│    │                                                                 │
│    ▼                                                                 │
│  staticfiles/DE-addresses.osm.pbf (~200-400MB)                      │
│    │                                                                 │
│    ▼                                                                 │
│  Upload to static.osmosis.page/osm/                                 │
│    │                                                                 │
│    ▼                                                                 │
│  Update links.toml pbf_url field                                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    Flow 2: Library                                   │
│                                                                      │
│  Address("Friesenstrasse 19, Berlin")                               │
│    │                                                                 │
│    ▼                                                                 │
│  Check if minified PBF exists locally                               │
│    │                                                                 │
│    ▼ (if missing)                                                   │
│  Read pbf_url from links.toml                                       │
│    │                                                                 │
│    ▼                                                                 │
│  Download from static.osmosis.page/osm/DE-addresses.osm.pbf         │
│    │                                                                 │
│    ▼                                                                 │
│  Query PBF with pyosmium                                            │
│    │                                                                 │
│    ▼                                                                 │
│  Return Address object                                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Flow 1: CI/CD - PBF Minification

Triggered when:
- `osm-filter-spec.md` changes (filter rules updated)
- Manually triggered (e.g., to pick up new Geofabrik data)

### Usage

```bash
# Create minified PBF for Germany
.tools/create_minified_pbf.sh DE staticfiles/DE-addresses.osm.pbf

# Create minified PBF for Austria
.tools/create_minified_pbf.sh AT staticfiles/AT-addresses.osm.pbf
```

### What the script does

```
links.toml
    │  read source_url for country
    ▼
Download from Geofabrik
    │  germany-latest.osm.pbf (~4GB)
    ▼
osmium tags-filter
    │  keeps only: addr:*, place=*, boundary=administrative, name
    │  (see osm-filter-spec.md for full list)
    ▼
staticfiles/
    │  DE-addresses.osm.pbf (~200-400MB)
    │  DE-addresses.osm.pbf.md5
    ▼
Upload to static.osmosis.page/osm/  (manual for now)
    │
    ▼
Update links.toml
    │  set pbf_url = "https://static.osmosis.page/osm/DE-addresses.osm.pbf"
    │  set checksum_url = "https://static.osmosis.page/osm/DE-addresses.osm.pbf.md5"
```

## Flow 2: Library - Address Standardization

Triggered on every `Address(raw_string)` call. **Not aware of Flow 1.**

```
Address("Friesenstrasse 19, Berlin", data_dir="~/.address-standardizer/")
    │
    ▼
Check: does DE-addresses.osm.pbf exist at data_dir?
    │
    ├─ NO ──▶ Read pbf_url from links.toml
    │              │
    │              ▼
    │         Download from static.osmosis.page
    │              │
    │              ▼
    │         Save to data_dir
    │
    ▼
Query minified PBF with pyosmium
    │  search for matching street, housenumber, city
    ▼
Return Address object:
    Address(
        street="Friesenstraße",
        housenumber="19",
        postcode="10965",
        city="Berlin",
        country="DE",
        raw="Friesenstrasse 19, Berlin"
    )
```

## File Roles

| File | Flow | Purpose |
|------|------|---------|
| `links.toml` | Both | Source URLs (Flow 1) and minified URLs (Flow 2) |
| `osm-filter-spec.md` | Flow 1 | Defines which OSM tags to keep/remove |
| `.tools/create_minified_pbf.sh` | Flow 1 | Script to download, minify, and output PBF |
| `staticfiles/` | Flow 1 | Local output directory for minified PBF before upload |
| `address_standardizer/address.py` | Flow 2 | Address class - main entry point |
| `address_standardizer/osm/downloader.py` | Flow 2 | Downloads minified PBF using pbf_url |
| `address_standardizer/osm/query.py` | Flow 2 | Queries PBF with pyosmium |

## links.toml Schema

```toml
[meta]
schema_version = "1"
last_updated = "2024-01-15T12:00:00Z"

[countries.DE]
name = "Germany"
# Used by Flow 1 (CI/CD) to download full PBF
source_url = "https://download.geofabrik.de/europe/germany-latest.osm.pbf"
source_checksum = "https://download.geofabrik.de/europe/germany-latest.osm.pbf.md5"
# Used by Flow 2 (Library) - updated by Flow 1 after minification
pbf_url = "https://static.osmosis.page/osm/DE-addresses.osm.pbf"
checksum_url = "https://static.osmosis.page/osm/DE-addresses.osm.pbf.md5"
```

## Local Data Directory

Default: `~/.address-standardizer/`

Can be overridden on class init:
```python
addr = Address("Friesenstrasse 19", data_dir="/custom/path/")
```

Contents:
```
~/.address-standardizer/
    DE-addresses.osm.pbf    # Downloaded minified PBF
    FR-addresses.osm.pbf    # (future)
    ...
```
