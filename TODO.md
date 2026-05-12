# TODO

## Hosting & Infrastructure

### Static File Hosting (Manual for now)
- [ ] Generate minified Germany PBF using osmium (see `osm-filter-spec.md`)
- [ ] Upload to `static.osmosis.page/osm/DE-addresses.osm.pbf`
- [ ] Upload MD5 checksum to `static.osmosis.page/osm/DE-addresses.osm.pbf.md5`
- [ ] Test download from static.osmosis.page works

### CI/CD Pipeline (Future)
- [ ] Automate minification triggered by changes to `osm-filter-spec.md`
- [ ] Automate upload to static.osmosis.page
- [ ] Extend pipeline to additional countries

## Country Support

### Currently available (in links.toml)
- `DE` - Germany ← only country with minified PBF for now

### Countries to add (after minified PBF is generated)
- `AT` - Austria       → Geofabrik: `europe/austria-latest.osm.pbf`
- `CH` - Switzerland   → Geofabrik: `europe/switzerland-latest.osm.pbf`
- `NL` - Netherlands   → Geofabrik: `europe/netherlands-latest.osm.pbf`
- `FR` - France        → Geofabrik: `europe/france-latest.osm.pbf`
- `GB` - Great Britain → Geofabrik: `europe/great-britain-latest.osm.pbf`
- `US` - United States → Geofabrik: `north-america/us-latest.osm.pbf`

### Notes
- Minified PBFs are ~90-95% smaller than full Geofabrik files
- See `osm-filter-spec.md` for what tags are kept/removed
- Geofabrik source: https://download.geofabrik.de/
- Static hosting: https://static.osmosis.page/osm/
