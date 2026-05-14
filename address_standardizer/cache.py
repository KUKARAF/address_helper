"""Simple LRU cache for address lookups."""

from functools import lru_cache
from pathlib import Path

from .query import AddressMatch, query_pbf


@lru_cache(maxsize=1000)
def cached_query(pbf_path: str, search_query: str) -> tuple[AddressMatch, ...]:
    """Query PBF with LRU caching (up to 1000 unique queries)."""
    results = query_pbf(Path(pbf_path), search_query, verbose=False)
    return tuple(results)


def clear_cache() -> None:
    """Clear the query cache."""
    cached_query.cache_clear()


def cache_info() -> dict:
    """Get cache statistics."""
    info = cached_query.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "size": info.currsize,
        "maxsize": info.maxsize,
    }
