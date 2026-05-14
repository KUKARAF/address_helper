"""Query OSM PBF files for address data."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import osmium


@dataclass
class AddressMatch:
    """An address match found in the PBF file."""

    street: Optional[str] = None
    housenumber: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

    def __str__(self) -> str:
        """Format address as a single string."""
        parts = []
        if self.street and self.housenumber:
            parts.append(f"{self.street} {self.housenumber}")
        elif self.street:
            parts.append(self.street)
        if self.postcode:
            parts.append(self.postcode)
        if self.city:
            parts.append(self.city)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)

    def is_complete(self) -> bool:
        """Check if address has minimum required fields."""
        return bool(self.street and self.city)


class AddressHandler(osmium.SimpleHandler):
    """Handler to find addresses in OSM data."""

    def __init__(self, search_query: str, max_matches: int = 10):
        super().__init__()
        self.search_query = search_query.lower()
        self.search_parts = [p.strip() for p in search_query.lower().split()]
        self.matches: list[AddressMatch] = []
        self.max_matches = max_matches
        self.node_count = 0

    def node(self, n: Any) -> None:
        """Process OSM nodes."""
        self.node_count += 1

        if len(self.matches) >= self.max_matches:
            return

        if not n.tags:
            return

        tags = dict(n.tags)
        if "addr:street" not in tags:
            return

        street = tags.get("addr:street", "").lower()
        if not any(part in street for part in self.search_parts):
            return

        match = AddressMatch(
            street=tags.get("addr:street"),
            housenumber=tags.get("addr:housenumber"),
            postcode=tags.get("addr:postcode"),
            city=tags.get("addr:city"),
            country=tags.get("addr:country"),
        )
        self.matches.append(match)

    def way(self, w: Any) -> None:
        """Process OSM ways."""
        if len(self.matches) >= self.max_matches:
            return

        if not w.tags:
            return

        tags = dict(w.tags)
        if "addr:street" not in tags:
            return

        street = tags.get("addr:street", "").lower()
        if not any(part in street for part in self.search_parts):
            return

        match = AddressMatch(
            street=tags.get("addr:street"),
            housenumber=tags.get("addr:housenumber"),
            postcode=tags.get("addr:postcode"),
            city=tags.get("addr:city"),
            country=tags.get("addr:country"),
        )
        self.matches.append(match)


def query_pbf(pbf_path: Path, search_query: str, verbose: bool = False) -> list[AddressMatch]:
    """
    Query PBF file for addresses matching the search query.

    Args:
        pbf_path: Path to the PBF file
        search_query: Address string to search for
        verbose: Enable progress output

    Returns:
        List of matching addresses
    """
    if verbose:
        print(f"Searching PBF for '{search_query}'...", flush=True)
    handler = AddressHandler(search_query, max_matches=10)
    handler.apply_file(str(pbf_path), locations=True)
    if verbose:
        print(f"Found {len(handler.matches)} matches", flush=True)
    return handler.matches
