"""
DEPRECATED: This module is superseded by db.py.

The in-memory indexing approach loads the entire 166M-node dataset into RAM,
which causes out-of-memory errors on systems with < 4GB available.

Use AddressDB (db.py) instead: it streams the PBF to SQLite in batches,
avoiding memory bloat and providing fast <100ms queries with full index.

This module is preserved for reference but is not called by the main Address flow.
"""

import pickle
from pathlib import Path
from typing import Any, Optional

from .query import AddressMatch, AddressHandler


class IndexBuilder(AddressHandler):
    """Build a searchable index of all addresses in the PBF file."""

    def __init__(self):
        super().__init__("")
        self.index: dict[str, list[AddressMatch]] = {}

    def node(self, n: Any) -> None:
        """Index all address nodes."""
        if not n.tags:
            return

        tags = dict(n.tags)
        if "addr:street" not in tags:
            return

        street = tags.get("addr:street", "").lower()
        match = AddressMatch(
            street=tags.get("addr:street"),
            housenumber=tags.get("addr:housenumber"),
            postcode=tags.get("addr:postcode"),
            city=tags.get("addr:city"),
            country=tags.get("addr:country"),
        )

        if street not in self.index:
            self.index[street] = []
        self.index[street].append(match)

    def way(self, w: Any) -> None:
        """Index all address ways."""
        if not w.tags:
            return

        tags = dict(w.tags)
        if "addr:street" not in tags:
            return

        street = tags.get("addr:street", "").lower()
        match = AddressMatch(
            street=tags.get("addr:street"),
            housenumber=tags.get("addr:housenumber"),
            postcode=tags.get("addr:postcode"),
            city=tags.get("addr:city"),
            country=tags.get("addr:country"),
        )

        if street not in self.index:
            self.index[street] = []
        self.index[street].append(match)


class AddressIndex:
    """Searchable index of addresses from a PBF file."""

    def __init__(self, pbf_path: Path, cache_path: Optional[Path] = None):
        self.pbf_path = pbf_path
        self.cache_path = cache_path or pbf_path.parent / f".{pbf_path.stem}.index.pkl"
        self.index: dict[str, list[AddressMatch]] = {}
        self._load_or_build()

    def _load_or_build(self) -> None:
        """Load cached index or build from PBF."""
        if self.cache_path.exists():
            print(f"Loading cached index from {self.cache_path.name}...", flush=True)
            with open(self.cache_path, "rb") as f:
                self.index = pickle.load(f)
            print(f"Loaded {len(self.index):,} streets", flush=True)
            return

        print(f"Building index from {self.pbf_path.name}...", flush=True)
        builder = IndexBuilder()
        builder.apply_file(str(self.pbf_path), locations=True)
        self.index = builder.index
        print(f"Built index with {len(self.index):,} streets", flush=True)

        # Cache for next time
        print(f"Caching index to {self.cache_path.name}...", flush=True)
        with open(self.cache_path, "wb") as f:
            pickle.dump(self.index, f)
        print("Index cached", flush=True)

    def search(self, query: str) -> list[AddressMatch]:
        """Search for addresses matching the query."""
        query_lower = query.lower()
        query_parts = [p.strip() for p in query_lower.split()]

        results: list[AddressMatch] = []
        for street, addresses in self.index.items():
            if any(part in street for part in query_parts):
                results.extend(addresses[:10])  # Limit per street
                if len(results) >= 10:
                    return results[:10]

        return results
