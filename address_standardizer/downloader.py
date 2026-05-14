"""Download and cache OSM PBF files and databases."""

import os
from pathlib import Path
from typing import Optional

import requests

from .models.region import get_country_region


def get_cache_dir() -> Path:
    """Get the cache directory for PBF files, creating it if needed."""
    cache_dir = Path.home() / ".address-standardizer"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def download_pbf(iso_code: str, force: bool = False) -> Path:
    """
    Download PBF file for a country if not cached locally.

    Args:
        iso_code: ISO 3166-1 alpha-2 country code (e.g., "DE")
        force: Re-download even if file exists locally

    Returns:
        Path to the local PBF file
    """
    region = get_country_region(iso_code)
    preferred = region.preferred_file

    cache_dir = get_cache_dir()
    cache_file = cache_dir / preferred.cache_filename

    if cache_file.exists() and not force:
        return cache_file

    print(f"Downloading {iso_code} PBF from {preferred.url}...")
    response = requests.get(preferred.url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(cache_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                    print(f"  {percent:.1f}%", end="\r")

    print(f"  Downloaded to {cache_file}")
    return cache_file


def get_pbf_path(iso_code: str, force: bool = False) -> Path:
    """
    Get path to PBF file, downloading if necessary.

    Args:
        iso_code: ISO 3166-1 alpha-2 country code
        force: Re-download if file exists

    Returns:
        Path to the PBF file
    """
    # Check if file exists in repo root first (for development/testing)
    repo_pbf = Path(__file__).parent.parent / f"{iso_code}-addresses.osm.pbf"
    if repo_pbf.exists():
        return repo_pbf

    cache_dir = get_cache_dir()
    region = get_country_region(iso_code)
    cache_file = cache_dir / region.preferred_file.cache_filename

    if cache_file.exists() and not force:
        return cache_file

    return download_pbf(iso_code, force=force)


def get_db_url(iso_code: str, override_url: Optional[str] = None) -> str:
    """
    Get the database URL for a country.

    Precedence (highest to lowest):
    1. override_url parameter (if provided)
    2. DB_URL environment variable
    3. db_url from links.toml (default from static.osmosis.page)

    Args:
        iso_code: ISO 3166-1 alpha-2 country code
        override_url: Optional explicit URL to use

    Returns:
        URL to download the database from

    Raises:
        ValueError: If no URL is available and none is provided
    """
    if override_url:
        return override_url

    env_url = os.environ.get("DB_URL")
    if env_url:
        return env_url

    region = get_country_region(iso_code)
    if hasattr(region, "db_url") and region.db_url:
        return region.db_url

    raise ValueError(
        f"No database URL available for {iso_code}. "
        "Set DB_URL environment variable or provide override_url parameter."
    )
