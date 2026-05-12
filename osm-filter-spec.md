# OSM Data Filter Specification

This document defines which OpenStreetMap tags and elements are needed for address standardization, and which can be removed to create a smaller, address-focused PBF file.

## Required Tags (KEEP)

### Address Tags
These are the primary tags needed for address parsing and standardization:

| Tag | Description | Example |
|-----|-------------|---------|
| `addr:street` | Street name | `Friesenstraße` |
| `addr:housenumber` | House/building number | `19`, `19a`, `19-21` |
| `addr:city` | City/town name | `Berlin` |
| `addr:postcode` | Postal/ZIP code | `10965` |
| `addr:country` | Country code | `DE` |
| `addr:suburb` | Suburb/district | `Kreuzberg` |
| `addr:district` | District | `Friedrichshain-Kreuzberg` |
| `addr:state` | State/province | `Berlin` |
| `addr:unit` | Unit/apartment number | `Apt 4` |
| `addr:floor` | Floor number | `3` |
| `addr:full` | Full address string | (fallback) |

### Place Tags
Needed for resolving city/town names and administrative hierarchies:

| Tag | Description |
|-----|-------------|
| `place=city` | City |
| `place=town` | Town |
| `place=village` | Village |
| `place=suburb` | Suburb |
| `place=neighbourhood` | Neighbourhood |
| `place=hamlet` | Hamlet |
| `place=locality` | Named locality |

### Administrative Boundaries
Needed for resolving administrative hierarchies and validating locations:

| Tag | Description |
|-----|-------------|
| `boundary=administrative` | Administrative boundary |
| `admin_level=*` | Admin level (2=country, 4=state, 6=county, 8=city, etc.) |

### Names
Required for matching place names:

| Tag | Description |
|-----|-------------|
| `name` | Primary name |
| `name:*` | Localized names (e.g., `name:en`, `name:de`) |
| `official_name` | Official name |
| `alt_name` | Alternative name |
| `old_name` | Historical name |

### Postal Codes
For postal code boundaries (where available):

| Tag | Description |
|-----|-------------|
| `boundary=postal_code` | Postal code boundary |
| `postal_code` | Postal code value |

## Optional Tags (KEEP if present)

These tags provide additional context but are not strictly required:

| Tag | Description |
|-----|-------------|
| `is_in` | Location hierarchy hint |
| `is_in:*` | Specific hierarchy (e.g., `is_in:city`) |

## Tags to REMOVE

All other tags should be removed to minimize file size. Major categories to strip:

### Remove - Physical Features
- `highway=*` (except nodes with address tags)
- `building=*` geometry (keep only if has `addr:*` tags)
- `landuse=*`
- `natural=*`
- `waterway=*`
- `railway=*`
- `aeroway=*`
- `power=*`
- `man_made=*`

### Remove - Points of Interest
- `amenity=*` (unless has address tags)
- `shop=*` (unless has address tags)
- `tourism=*`
- `leisure=*`
- `sport=*`
- `historic=*`

### Remove - Metadata
- `source=*`
- `created_by=*`
- `note=*`
- `fixme=*`
- `FIXME=*`
- `description=*`

### Remove - Routing/Navigation
- `turn:*`
- `lanes=*`
- `maxspeed=*`
- `oneway=*`
- `surface=*`
- `access=*`

### Remove - Rendering
- `layer=*`
- `level=*` (unless related to address)
- `height=*`
- `building:levels=*`
- `roof:*`
- `colour=*`
- `material=*`

## osmium tags-filter Command

To create a minified PBF with only address-relevant data:

```bash
osmium tags-filter input.osm.pbf \
    addr:street \
    addr:housenumber \
    addr:city \
    addr:postcode \
    addr:country \
    addr:suburb \
    addr:district \
    addr:state \
    addr:unit \
    addr:floor \
    addr:full \
    place=city \
    place=town \
    place=village \
    place=suburb \
    place=neighbourhood \
    place=hamlet \
    place=locality \
    boundary=administrative \
    boundary=postal_code \
    postal_code \
    name \
    -o output.osm.pbf
```

Or using a shorter expression:

```bash
osmium tags-filter input.osm.pbf \
    "addr:*" \
    "place=city,town,village,suburb,neighbourhood,hamlet,locality" \
    "boundary=administrative,postal_code" \
    "postal_code" \
    "name" \
    -o output.osm.pbf
```

## Expected Size Reduction

| Country | Full PBF | Minified PBF | Reduction |
|---------|----------|--------------|-----------|
| Germany | ~4.0 GB  | ~200-400 MB  | ~90-95%   |

## Notes

1. **Geometry**: Keep node coordinates for all retained elements. Ways and relations with address tags should retain their member references.

2. **Relations**: Keep administrative boundary relations intact (they define city/district boundaries).

3. **Interpolation**: Consider keeping `addr:interpolation` ways if present - these define house number sequences along streets.

4. **Updates**: Minified files should be regenerated weekly to pick up OSM updates.
