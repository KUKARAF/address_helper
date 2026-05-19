"""Download and cache OSM address databases."""

import hashlib
import os
from pathlib import Path
from typing import Optional

import requests

from .models.region import get_country_region


def get_cache_dir() -> Path:
    """Get the cache directory for address database files, creating it if needed."""
    cache_dir = Path.home() / ".address-standardizer"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_db_url(iso_code: str, override_url: Optional[str] = None) -> str:
    """
    Get the database URL for a country.

    Precedence (highest to lowest):
    1. override_url parameter (if provided)
    2. DB_URL environment variable
    3. db_url from links.toml for the country

    Args:
        iso_code: ISO 3166-1 alpha-2 country code
        override_url: Optional explicit URL to use

    Returns:
        URL to download the database from
    """
    if override_url:
        return override_url

    env_url = os.environ.get("DB_URL")
    if env_url:
        return env_url

    region = get_country_region(iso_code)
    if not region.db_url:
        raise ValueError(f"No db_url configured for country '{iso_code}' in links.toml")
    return region.db_url


def get_db_cache_path(iso_code: str) -> Path:
    """Return the version-keyed local cache path for the pre-built DB."""
    from . import __version__

    return get_cache_dir() / f"{iso_code.upper()}-addresses.osm.db.v{__version__}"


def _compute_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch_expected_md5(md5_url: str) -> Optional[str]:
    """Fetch expected MD5 from a .md5 sidecar URL. Returns None on any failure."""
    try:
        r = requests.get(md5_url, timeout=10)
        r.raise_for_status()
        return r.text.strip().split()[0]
    except Exception:
        return None


def download_db(iso_code: str, force: bool = False) -> Path:
    """
    Get the pre-built SQLite DB for a country, downloading if not cached.

    Cache is keyed by package version (~/.address-standardizer/DE-addresses.osm.db.v0.1.0),
    so upgrading the package automatically fetches the matching DB on next use.

    Args:
        iso_code: ISO 3166-1 alpha-2 country code
        force: Re-download even if a cached version exists

    Returns:
        Path to the local DB file
    """
    # CI build workflow: use a local file directly, bypassing all download logic
    env_path = os.environ.get("ADDRESS_STANDARDIZER_DB_PATH")
    if env_path:
        return Path(env_path)

    cache_path = get_db_cache_path(iso_code)

    if cache_path.exists() and not force:
        print(f"Using cached DB at {cache_path}", flush=True)
        return cache_path

    region = get_country_region(iso_code)
    url = get_db_url(iso_code)
    tmp_path = cache_path.with_suffix(".tmp")

    print(f"Downloading DB from {url}...", flush=True)
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(tmp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        print(f"  {downloaded / total_size * 100:.1f}%", end="\r", flush=True)

        # Use checksum from links.toml if available, otherwise try .md5 sidecar URL
        expected_md5 = region.db_checksum or _fetch_expected_md5(url + ".md5")
        if expected_md5:
            actual_md5 = _compute_md5(tmp_path)
            if actual_md5 != expected_md5:
                raise ValueError(
                    f"MD5 mismatch for {cache_path.name}: expected {expected_md5}, got {actual_md5}"
                )

        tmp_path.rename(cache_path)
        print(f"\nDownloaded to {cache_path}", flush=True)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    return cache_path
