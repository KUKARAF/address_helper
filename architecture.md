# Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        address-standardizer repo                     │
│                                                                      │
│  links.toml          ← updated by CI/CD in ../static repo           │
│  address_standardizer/                                               │
│    models/region.py  ← reads links.toml at import time              │
│    osm/downloader.py ← uses preferred_file URL from region          │
└─────────────────────────────────────────────────────────────────────┘
         │                                        ▲
         │ pip install                            │ git commit links.toml
         ▼                                        │
┌─────────────────┐              ┌────────────────────────────────────┐
│  User App       │              │  ../static repo  (CI/CD pipeline)  │
│                 │              │                                     │
│  Address("...")  │              │  .tools/create_..._pbf.sh          │
└─────────────────┘              │    1. Download from Geofabrik       │
                                 │    2. osmium tags-filter            │
                                 │    3. Upload to static.osmosis.page │
                                 │    4. Update links.toml             │
                                 │    5. Commit + push                 │
                                 └────────────────────────────────────┘
                                              │ upload
                                              ▼
                                 ┌────────────────────────────────────┐
                                 │  static.osmosis.page               │
                                 │  (S3 or static file server)        │
                                 │                                     │
                                 │  DE-addresses-latest.osm.pbf       │
                                 │  DE-addresses-latest.osm.pbf.md5   │
                                 └────────────────────────────────────┘
                                              │ download (first run)
                                              ▼
                                 ┌────────────────────────────────────┐
                                 │  ~/.address-standardizer/          │
                                 │    DE-addresses-latest.osm.pbf     │
                                 │    cache.sqlite                    │
                                 └────────────────────────────────────┘
```

## Data Pipeline

### Step 1: Minification (CI/CD in `../static` repo)
Runs on a schedule (e.g. weekly) or manually triggered.

```
Geofabrik PBF (~4GB)
    │
    ▼
osmium tags-filter
    │  keeps: addr:*, name, place=*, boundary=administrative, buildings
    ▼
Minified PBF (~200-400MB)
    │
    ▼
Upload to static.osmosis.page
    │
    ▼
Update links.toml → commit → push to address-standardizer repo
```

### Step 2: User Download (library, first run per country)
```
links.toml
    │  preferred_file = minified if available, else full Geofabrik
    ▼
Download PBF to ~/.address-standardizer/
    │  verify MD5 checksum
    ▼
Parse with pyosmium → extract address rows
    │
    ▼
Store in ~/.address-standardizer/cache.sqlite
    │  indexes on: street, postcode, city
    ▼
PBF file can be deleted (optional, configurable)
```

### Step 3: Address Lookup (library, every call)
```
Address("Friesenstrasse 19, Berlin")
    │
    ▼
Query cache.sqlite
    │  SELECT * FROM addresses WHERE street LIKE ? AND city LIKE ?
    ▼
Return structured AddressComponents
```

## File Roles

| File | Repo | Purpose |
|------|------|---------|
| `links.toml` | address-standardizer | Maps country codes → download URLs. Source of truth for what's available. |
| `address_standardizer/models/region.py` | address-standardizer | Reads `links.toml`, exposes `get_country_region()` |
| `address_standardizer/osm/downloader.py` | address-standardizer | Downloads PBF using URL from `region.preferred_file` |
| `.tools/create_street_postcode_city_only_pbf.sh` | address-standardizer | CI/CD entry point: download → filter → upload → update toml |
| `.tools/create_street_postcode_city_only_pbf.py` | address-standardizer | Updates `links.toml` fields after upload |

## links.toml Schema

```toml
[meta]
schema_version = "1"
static_base_url = "https://static.osmosis.page/osm"
last_updated = "2024-01-15T12:00:00Z"

[countries.DE]
name = "Germany"
full = "https://download.geofabrik.de/europe/germany-latest.osm.pbf"
full_checksum = "https://download.geofabrik.de/europe/germany-latest.osm.pbf.md5"
minified = "https://static.osmosis.page/osm/DE-addresses-latest.osm.pbf"
minified_checksum = "https://static.osmosis.page/osm/DE-addresses-latest.osm.pbf.md5"
minified_size_mb = 210.4
last_minified = "2024-01-15T12:00:00Z"
```

## CI/CD Trigger Strategy

The minification pipeline should run:
- **Weekly** (cron) to pick up OSM data updates from Geofabrik
- **Manually** when a new country is added to `links.toml`
- **On push** to `../static` repo if osmium filter expressions change

After a successful run, the pipeline commits the updated `links.toml` back
to the `address-standardizer` repo. Library users get the new URL on their
next cache refresh (controlled by `cache_ttl_days` in settings).
