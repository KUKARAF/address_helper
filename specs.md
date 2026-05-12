# address-standardizer

## Overview
Address-standardizer is a Python library that parses and standardizes address strings using OpenStreetMap (OSM) data. It provides an address class that can be initialized with a raw address string, identifies the correct location using OSM's search logic, and returns a standardized address with structured components (street, city, country, etc.). The library downloads OSM data to a local cache for offline reuse, with support for downloading specific regions on demand.

## Goals & Non-Goals

### Goals
- Provide a simple, intuitive `Address` class interface for address standardization
- Match the same search logic and results as the OpenStreetMap website
- Download and cache OSM data locally for offline use after initial download
- Support downloading specific country/region datasets as needed
- Handle international address formats using OSM's global dataset
- Return structured address components (street, city, postal code, country, etc.)
- Achieve high accuracy for address matching within supported regions

### Non-Goals
- Providing a REST API or web service (library only)
- Real-time address validation without cached data
- Geocoding coordinates (reverse or forward)
- Address autocomplete/suggestions
- Integration with other geocoding services
- Administrative boundary validation beyond OSM data

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Application                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           address_standardizer Library              │   │
│  │                                                     │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│  │  │   Address   │  │   OSMData    │  │   Cache    │ │   │
│  │  │   Class     │──│   Manager    │──│   Layer    │ │   │
│  │  │             │  │              │  │            │ │   │
│  │  └─────────────┘  └──────────────┘  └────────────┘ │   │
│  │          │                   │              │      │   │
│  │  ┌──────────────┐    ┌──────────────┐      │      │   │
│  │  │  Validator   │    │  Normalizer  │      │      │   │
│  │  │   Logic      │    │   Logic      │      │      │   │
│  │  └──────────────┘    └──────────────┘      │      │   │
│  └─────────────────────────────────────────────│──────┘   │
│                                                │          │
└────────────────────────────────────────────────│──────────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │    Local Cache Dir      │
                                    │    (~/.address-std/)    │
                                    │  ┌──────────────────┐   │
                                    │  │  country1.pbf    │   │
                                    │  │  country2.pbf    │   │
                                    │  │  cache.sqlite    │   │
                                    │  └──────────────────┘   │
                                    └─────────────────────────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │   OSM Servers/APIs      │
                                    │  (download.geofabrik.de)│
                                    │  (overpass-api.de)      │
                                    └─────────────────────────┘
```

### Data Flow
1. User instantiates `Address(raw_string="Friesenstrasse 19")`
2. Library checks if required region data exists in local cache
3. If missing, downloads specific region data from OpenStreetMap servers
4. Parses address using OSM's search logic against cached data
5. Returns structured, standardized address components
6. Subsequent calls reuse cached data for same region

## Stack

### Core
- **Python**: 3.13.3 (as specified) - will support 3.10+ for broader compatibility
- **Framework**: None (pure library) - FastAPI/Django would add unnecessary overhead
- **Key libraries**:
  - `pyosmium` - For reading and querying OSM PBF files efficiently
  - `shapely` - For spatial operations if bounding box queries are needed
  - `pydantic` - For typed data models and address component validation
  - `requests` / `httpx` - For downloading OSM data files
  - `lxml` / `xml.etree` - For parsing OSM XML if needed
  - `python-dateutil` - For handling timestamps in OSM data

### Data
- **Database**: SQLite for local cache - lightweight, no external dependencies
- **ORM**: SQLAlchemy 2.x (async optional) - for structured cache queries
- **Cache strategy**: Local filesystem with SQLite metadata
  - OSM PBF files stored as downloaded
  - Processed address data indexed in SQLite for fast lookups
  - Configurable cache location with default at `~/.address-standardizer/`

### Dev tooling
- **Package manager**: `uv` - fast, modern, supports locking and virtualenvs
- **Linting/formatting**: `ruff` (replaces flake8 + isort + pyupgrade)
- **Type checking**: `mypy` with strict mode for type safety
- **Testing**: `pytest` + `pytest-cov` + `pytest-asyncio` (if async)
- **Pre-commit hooks**: ruff, mypy, pytest on changed files
- **Task runner**: `Makefile` for common development commands
- **Documentation**: `mkdocs` or `sphinx` with autodoc

### Infrastructure
- **Containerization**: Docker for testing and CI, not for deployment
- **Deployment target**: PyPI package, installable via pip
- **CI**: GitHub Actions for testing, linting, and publishing
- **Secrets management**: None needed (public OSM data)
- **Package registry**: PyPI for releases, GitHub Packages for dev builds

> ⚠️ **TBD: Async vs Sync**
> Need to decide if the library should be async-native. OSM file parsing is CPU-bound, but network downloads benefit from async.
> Recommendation: Provide both sync and async interfaces using `asyncio.to_thread` for heavy operations.

## Project Structure

```
address_standardizer/
├── __init__.py              # Main exports: Address class
├── address.py               # Address class implementation
├── osm/                     # OSM data handling
│   ├── __init__.py
│   ├── downloader.py       # OSM data download utilities
│   ├── parser.py           # PBF/XML parsing
│   ├── cache.py           # Cache management
│   └── query.py           # Address search logic
├── models/                  # Data models
│   ├── __init__.py
│   ├── address.py          # Address components (Pydantic)
│   └── region.py           # Region/country definitions
├── utils/                   # Utilities
│   ├── __init__.py
│   ├── validation.py       # Address validation helpers
│   └── normalizer.py       # String normalization
├── config.py               # Configuration management
├── exceptions.py           # Custom exceptions
└── cli/                    # Optional CLI for testing
    ├── __init__.py
    └── main.py

tests/
├── __init__.py
├── conftest.py             # Pytest fixtures
├── test_address.py         # Address class tests
├── test_osm_downloader.py  # OSM download tests
├── test_osm_parser.py      # Parser tests
└── test_integration.py     # Integration tests

docs/
├── index.md
├── api.md                  # API documentation
└── examples.md             # Usage examples

scripts/
├── download_osm.py         # Scripts for manual OSM downloads
└── update_cache.py         # Cache management scripts

pyproject.toml              # Project config (uv/poetry)
Makefile                    # Development commands
README.md                   # Project description
LICENSE                     # MIT/Apache2
.gitignore
.pre-commit-config.yaml
.github/
└── workflows/
    ├── test.yml
    └── publish.yml
```

### Directory Rationale
- `address_standardizer/` - Main package following snake_case convention
- `osm/` - Isolated OSM-specific logic for maintainability
- `models/` - Clean separation of data structures from business logic
- `tests/` - Separate test directory following Python conventions
- `docs/` - Documentation separate from code
- `scripts/` - Administrative scripts not part of the library
- `.github/` - CI/CD configuration

## Environment & Config

Configuration uses `pydantic-settings` for typed, validated environment variables:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Cache configuration
    cache_dir: Path = Path.home() / ".address-standardizer"
    cache_ttl_days: int = 30  # How long to keep downloaded data
    
    # OSM download settings
    osm_download_url: str = "https://download.geofabrik.de"
    user_agent: str = "address-standardizer/1.0.0"
    download_timeout: int = 300  # seconds
    
    # Performance settings
    max_cache_size_gb: int = 10
    search_parallelism: int = 1
    
    model_config = SettingsConfigDict(env_prefix="ADDR_STD_")
```

Required environment variables: None (all have defaults)

`.env.example`:
```bash
# Optional: Customize cache location
# ADDR_STD_CACHE_DIR=/path/to/cache

# Optional: Custom OSM download mirror
# ADDR_STD_OSM_DOWNLOAD_URL=https://custom-mirror.example.com

# Optional: Increase timeout for slow connections
# ADDR_STD_DOWNLOAD_TIMEOUT=600
```

## API / Interface Design

### Core Interface
```python
from address_standardizer import Address

# Basic usage
addr = Address("Friesenstrasse 19, Berlin")
print(addr.standardized)  # Structured address dict
print(addr.city)          # "Berlin"
print(addr.street)        # "Friesenstrasse"
print(addr.house_number)  # "19"

# With region hint (faster)
addr = Address("1600 Pennsylvania Ave", region="us")
```

### Class Methods
```python
# Check if region data is cached
Address.has_region_data("de")  # → bool

# Pre-download region data
await Address.download_region_data("de")  # Async
Address.download_region_data_sync("de")   # Sync

# Clear cache
Address.clear_cache(region="de")  # Specific region
Address.clear_cache()            # All regions
```

### Return Structure
```python
{
    "raw": "Friesenstrasse 19",
    "standardized": {
        "street": "Friesenstrasse",
        "house_number": "19",
        "city": "Berlin",
        "state": "Berlin",
        "postal_code": "10969",
        "country": "DE",
        "country_name": "Germany",
        "latitude": 52.501,
        "longitude": 13.419
    },
    "confidence": 0.95,
    "source": "openstreetmap",
    "region": "de"
}
```

## Data Models

### Address Components (Pydantic)
```python
class AddressComponents(BaseModel):
    street: Optional[str]
    house_number: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: str  # ISO 3166-1 alpha-2
    country_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    bounding_box: Optional[Tuple[float, float, float, float]]
```

### Cache Schema (SQLAlchemy)
```python
class OSMCache(Base):
    __tablename__ = "osm_cache"
    
    id = Column(Integer, primary_key=True)
    region = Column(String(2), index=True)  # ISO country code
    downloaded_at = Column(DateTime)
    file_path = Column(String)
    file_size = Column(Integer)
    data_version = Column(String)  # OSM data version/timestamp
    is_active = Column(Boolean, default=True)
```

## Key Design Decisions

### Decision: Local SQLite cache over in-memory only
- **Rationale**: Need to persist large OSM datasets (~GBs) between runs. SQLite provides structured querying and metadata management without external dependencies.
- **Alternatives considered**:
  - Pure filesystem cache: Harder to query and manage metadata
  - Redis: External dependency, overkill for local library
  - In-memory only: Would require re-downloading on every run

### Decision: Region-based downloads over global dataset
- **Rationale**: OSM global dataset is ~100GB+ compressed. Most users need specific countries. Region-based allows incremental downloads and smaller footprint.
- **Alternatives considered**:
  - Download global extract: Impractical for most users, long download times
  - Use Overpass API for queries: Requires internet, slower, rate-limited
  - Pre-packaged regional datasets: Hard to maintain, large package size

### Decision: PBF format over XML for OSM data
- **Rationale**: PBF is compact, faster to parse, and standard for OSM extracts. `pyosmium` provides efficient PBF reading.
- **Alternatives considered**:
  - OSM XML: Larger files, slower parsing
  - Overpass JSON: Requires API calls, not offline
  - Custom binary format: Would need converter, maintenance burden

### Decision: Sync-first with async option
- **Rationale**: Many Python applications are sync. Provide simple sync API by default with optional async methods for downloads.
- **Alternatives considered**:
  - Async-only: Forces async on all users, harder for sync codebases
  - Sync-only: Misses performance benefits for network operations
  - Separate sync/async packages: Maintenance overhead

### Decision: Pure Python library over service
- **Rationale**: Specified as library requirement. Simpler deployment, no network dependencies after caching, works offline.
- **Alternatives considered**:
  - REST API service: Would require running service, network calls
  - gRPC service: More complex, binary dependencies
  - CLI tool only: Less integrable into applications

## Development Workflow

### Initial Setup (3 commands)
```bash
# 1. Clone and enter
git clone https://github.com/username/address-standardizer
cd address-standardizer

# 2. Install with uv
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# 3. Install pre-commit hooks
pre-commit install
```

### Common Development Commands
```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Lint and type check
make lint
make type-check

# Run all checks (pre-commit)
make check

# Build package
make build

# Clean cache
make clean
```

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- Feature branches: `feature/description` or `fix/description`
- Release branches: `release/v1.2.0`

### PR Conventions
- PRs must pass all checks (lint, type, test)
- PRs require at least one review
- PR titles follow Conventional Commits: `feat:`, `fix:`, `docs:`, etc.
- PR descriptions include context, changes, testing done

## Testing Strategy

### Test Pyramid
- **Unit tests (70%)**: Individual components (address parsing, OSM query logic)
- **Integration tests (25%)**: Component interactions (download + parse + cache)
- **E2E tests (5%)**: Full address standardization workflows

### Mock Strategy
- **Mock network calls**: Use `responses` or `httpx.mock` for OSM downloads
- **Mock file system**: Use `pytest-mock` for cache operations
- **Use test fixtures**: Pre-downloaded small OSM extracts in `tests/fixtures/`

### Coverage Targets
- Overall: ≥85% line coverage
- Critical paths: ≥95% (address parsing, OSM query logic)
- Minimum: ≥80% for CI to pass

### Test Data
- Include small OSM extract for Germany (Berlin area) in test fixtures
- Use synthetic address data for unit tests
- Integration tests use real but minimal OSM data

## Performance & Scaling Considerations

### Known Bottlenecks
1. **Initial OSM download**: Large files (100MB-1GB per country)
   - Mitigation: Progress reporting, resume support, regional extracts
2. **PBF parsing**: CPU-intensive for large extracts
   - Mitigation: Index important fields in SQLite, lazy loading
3. **Memory usage**: Large OSM files in memory
   - Mitigation: Stream processing, chunked reads

### Optimization Strategy
  - Build spatial indexes for common queries
  - Cache frequent address lookups in memory LRU
  - Compress OSM data in cache (lz4/zstd)
  - Parallel parsing for multi-core systems

### Load Targets
- Single address lookup: < 100ms (after cache warm-up)
- Batch processing: 1000 addresses/second on moderate hardware
- Cache warm-up: < 5 minutes for typical country (~500MB)

### Memory Limits
- Target: < 500MB RAM for typical usage
- Peak: < 2GB during large file processing
- Cache size configurable, default 10GB disk

## Security Considerations

### Input Validation
- Validate all user inputs with Pydantic models
- Sanitize address strings to prevent injection attacks
- Validate region codes against ISO 3166-1 list

### Network Security
- Verify TLS certificates for OSM downloads
- Validate file checksums (MD5/SHA256 provided by OSM mirrors)
- Rate limiting for automatic retries

### Dependency Security
- Use `uv` with lockfile for reproducible builds
- Regular `pip-audit` scans in CI
- Dependabot for security updates
- Pin transitive dependencies where critical

### Data Privacy
- No telemetry or data collection
- Local cache only, no external transmission
- Clear cache command for data removal

### File System Security
- Secure cache directory permissions (user-only read/write)
- Validate file paths to prevent directory traversal
- Clean up temporary files promptly

## Open Questions / TBDs

1. **Region granularity**: Should we support sub-national regions (states/provinces) or only countries?
   - Recommendation: Start with countries, add states later if needed

2. **Update strategy**: How frequently should cached OSM data be refreshed?
   - Recommendation: Configurable TTL, default 30 days, with manual update method

3. **Language support**: How to handle multilingual addresses (e.g., street names in local + English)?
   - Recommendation: Return primary language from OSM, with option for translations

4. **Address completeness**: What to do with partial/incomplete addresses?
   - Recommendation: Return partial matches with confidence score, don't fail

5. **License compliance**: Ensure proper attribution for OSM data usage
   - Need to include OSM copyright notice in documentation

6. **Alternative data sources**: Should we support other geocoding services as fallback?
   - Recommendation: Not initially, but design interfaces to allow plugins later

7. **Benchmark dataset**: Need standard address test suite for accuracy measurement
   - Should create/open source test dataset with known correct standardized addresses

8. **Performance vs accuracy trade-off**: How aggressive to be with approximate matching?
   - Recommendation: Start with exact/precise matching, add fuzzy later as option

9. **API stability**: Versioning strategy for public API
   - Recommendation: Semantic versioning, deprecation warnings for breaking changes

10. **Documentation scope**: How detailed should usage examples be?
    - Recommendation: Comprehensive cookbook with common international address patterns