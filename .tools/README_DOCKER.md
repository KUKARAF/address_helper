# Docker Setup for PBF Minification

This directory contains Docker configuration for creating minified OSM PBF files containing only address-relevant data.

## Files

- **Dockerfile** - Contains osmium-tool and all dependencies
- **create_minified_pbf.sh** - Main script (now Docker-aware)
- **create_street_postcode_city_only_pbf.py** - Updates links.toml after upload

## Quick Start

### Option 1: Using Docker (Recommended)

Ensure Docker is installed:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

Then run:

```bash
# The script automatically uses Docker if available
.tools/create_minified_pbf.sh DE staticfiles/DE-addresses.osm.pbf
```

The script will:
1. Detect Docker is available
2. Build the Docker image automatically (first time only)
3. Download the full PBF from Geofabrik
4. Minify it using osmium-tool inside Docker
5. Generate checksums

### Option 2: Using Local Tools

If Docker is not available, the script will fall back to local tools:

```bash
# Install osmium-tool and Python dependencies
sudo apt-get install osmium-tool curl wget python3-pip
pip3 install tomli

# Run the script (will use local tools)
.tools/create_minified_pbf.sh DE staticfiles/DE-addresses.osm.pbf
```

### Option 3: Force Local Tools

To skip Docker detection and always use local tools:

```bash
export USE_DOCKER=false
.tools/create_minified_pbf.sh DE staticfiles/DE-addresses.osm.pbf
```

## How It Works

### Docker Flow

1. **Dockerfile** defines the image with:
   - osmium-tool (main minification tool)
   - curl/wget (for downloads)
   - Python 3 with tomli package

2. **create_minified_pbf.sh** is Docker-aware:
   - Detects if Docker is available
   - Builds the image automatically on first run
   - Runs the entire minification pipeline in a Docker container
   - Mounts your project directory at `/workspace`
   - Verifies output and generates checksums

3. The container:
   - Has isolated environment with all dependencies
   - Mounts the project directory for file access
   - Downloads PBF files
   - Outputs minified files directly to the host filesystem

## Key Advantages

- **Isolation**: osmium-tool and dependencies run in a container
- **Portability**: Works on any system with Docker
- **No Installation**: No need to install osmium-tool locally
- **Compatibility**: Handles different OS environments
- **Fallback**: Automatically falls back to local tools if Docker unavailable

## Troubleshooting

### Docker not starting
```bash
# Check if Docker service is running
sudo systemctl start docker

# Add your user to docker group (requires logout/login)
sudo usermod -aG docker $USER
```

### Image build fails
```bash
# Rebuild the image (skip cache)
docker build --no-cache -t address-helper:osm-minifier .tools/
```

### Permission denied errors
```bash
# Ensure Docker daemon is running
sudo systemctl start docker

# Or run with sudo
sudo .tools/create_minified_pbf.sh DE staticfiles/DE-addresses.osm.pbf
```

### Memory issues
If the download is slow or times out, Docker may need more memory. Increase Docker's memory limit in Docker Desktop settings or via daemon.json.

## Caching

The script automatically caches downloaded PBF files in `.osm-cache/` directory. This means:

- First run for a country: Downloads the full PBF file (~1-3 GB), minifies it, and caches the download
- Subsequent runs: Reuses the cached PBF file, skipping the download entirely

**Cache directory:**
```
address_helper/
├── .osm-cache/
│   ├── germany-latest.osm.pbf      # Cached full PBF for Germany
│   ├── france-latest.osm.pbf       # Cached full PBF for France
│   └── ...
├── .tools/
├── links.toml
└── staticfiles/
    └── DE-addresses.osm.pbf        # Minified output
```

**To clear the cache:**
```bash
rm -rf .osm-cache/
```

**To keep the cache but delete a specific country:**
```bash
rm .osm-cache/germany-latest.osm.pbf
```

## Environment Variables

- **USE_DOCKER** - Set to `false` to disable Docker and use local tools
  ```bash
  export USE_DOCKER=false
  .tools/create_minified_pbf.sh DE output.osm.pbf
  ```

## Files Modified

- `.tools/create_minified_pbf.sh` - Updated to support Docker execution and PBF caching
- `.tools/Dockerfile` - Created
- `.tools/README_DOCKER.md` - This file (added caching documentation)

## Next Steps

1. **Create a minified PBF** (Docker image builds automatically):
   ```bash
   .tools/create_minified_pbf.sh DE staticfiles/DE-addresses.osm.pbf
   ```

3. **Upload to static server** and update links.toml with the URLs

4. **Verify with**:
   ```bash
   .tools/create_street_postcode_city_only_pbf.py \
       --toml links.toml \
       --country DE \
       --minified-url https://static.osmosis.page/osm/DE-addresses-latest.osm.pbf \
       --minified-checksum https://static.osmosis.page/osm/DE-addresses-latest.osm.pbf.md5 \
       --minified-size-mb 210.4
   ```

## References

- [osmium-tool documentation](https://osmcode.org/osmium-tool/)
- [Docker documentation](https://docs.docker.com/)
- [docker-compose documentation](https://docs.docker.com/compose/)
