"""SQLite-backed address index built from an OSM PBF file or downloaded from a remote URL."""

import sqlite3
from pathlib import Path
from typing import Any, Optional

import osmium
import requests
from rapidfuzz import fuzz

from .postcode_filter import extract_postcode_from_address
from .query import AddressMatch

_BATCH_SIZE = 10_000


class _DBBuilder(osmium.SimpleHandler):
    """Stream address nodes/ways into SQLite in batches."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        super().__init__()
        self.conn = conn
        self._batch: list[tuple] = []

    def _flush(self) -> None:
        """Batch insert the current buffer and commit."""
        if not self._batch:
            return
        self.conn.executemany(
            "INSERT INTO addresses (street, street_lower, housenumber, postcode, city, country) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            self._batch,
        )
        self.conn.commit()
        self._batch.clear()

    def _handle_tags(self, tags: dict[str, str]) -> None:
        """Process address tags common to nodes and ways."""
        street = tags.get("addr:street")
        if not street:
            return

        row = (
            street,
            street.lower(),
            tags.get("addr:housenumber"),
            tags.get("addr:postcode"),
            tags.get("addr:city"),
            tags.get("addr:country"),
        )
        self._batch.append(row)

        if len(self._batch) >= _BATCH_SIZE:
            self._flush()

    def node(self, n: Any) -> None:
        """Process OSM nodes."""
        if not n.tags:
            return
        self._handle_tags(dict(n.tags))

    def way(self, w: Any) -> None:
        """Process OSM ways."""
        if not w.tags:
            return
        self._handle_tags(dict(w.tags))

    def finalize(self) -> None:
        """Flush any remaining buffered rows."""
        self._flush()


class AddressDB:
    """SQLite index for addresses from a PBF file or remote database."""

    def __init__(self, pbf_path: Path, db_url: Optional[str] = None) -> None:
        """
        Open or build the address index.

        If db_url is provided, download the pre-built database instead of building from PBF.
        Otherwise, DB is stored next to the PBF as pbf_path.with_suffix('.db').
        Builds if: DB does not exist, or PBF is newer than DB.

        Args:
            pbf_path: Path to the PBF file (used for local DB path)
            db_url: Optional URL to download pre-built database from
        """
        self.pbf_path = Path(pbf_path)
        self.db_path = self.pbf_path.with_suffix(".db")
        self.conn: Optional[sqlite3.Connection] = None

        if db_url:
            self._download_db(db_url)
        elif not self._db_is_fresh():
            self._build()

        self.conn = sqlite3.connect(str(self.db_path))

    @classmethod
    def from_path(cls, db_path: Path) -> "AddressDB":
        """Open a pre-existing DB file without any build or download logic."""
        db_path = Path(db_path)
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        instance = object.__new__(cls)
        instance.pbf_path = db_path.with_suffix(".pbf")  # placeholder, not used
        instance.db_path = db_path
        instance.conn = sqlite3.connect(str(db_path))
        return instance

    def _db_is_fresh(self) -> bool:
        """Return True if DB exists and is newer than (or equal to) PBF."""
        if not self.db_path.exists():
            return False
        pbf_mtime = self.pbf_path.stat().st_mtime
        db_mtime = self.db_path.stat().st_mtime
        return db_mtime >= pbf_mtime

    def _download_db(self, url: str) -> None:
        """Download pre-built database from a remote URL."""
        if self.db_path.exists():
            print(f"Using cached database at {self.db_path}", flush=True)
            return

        print(f"Downloading database from {url}...", flush=True)
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(self.db_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f"  {percent:.1f}%", end="\r", flush=True)

        print(f"\n✓ Database downloaded to {self.db_path}", flush=True)

    def _build(self) -> None:
        """Build the SQLite index from the PBF file."""
        print(f"Building index from {self.pbf_path.name}...", flush=True)

        # Remove stale DB if it exists
        if self.db_path.exists():
            self.db_path.unlink()

        conn = sqlite3.connect(str(self.db_path))

        # Optimize for bulk insert
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        # Create table
        conn.execute(
            """
            CREATE TABLE addresses (
                id           INTEGER PRIMARY KEY,
                street       TEXT NOT NULL,
                street_lower TEXT NOT NULL,
                housenumber  TEXT,
                postcode     TEXT,
                city         TEXT,
                country      TEXT
            )
            """
        )
        conn.commit()

        # Stream PBF into table (no indexes yet, for speed)
        builder = _DBBuilder(conn)
        builder.apply_file(str(self.pbf_path), locations=False)
        builder.finalize()

        # Create indexes after bulk insert
        print("Creating indexes...", flush=True)
        conn.execute("CREATE INDEX idx_postcode ON addresses(postcode)")
        conn.execute("CREATE INDEX idx_street_lower ON addresses(street_lower)")
        conn.execute("CREATE INDEX idx_postcode_street ON addresses(postcode, street_lower)")
        conn.commit()
        conn.close()

        print(f"Index built at {self.db_path}", flush=True)

    def search(
        self,
        query: str,
        max_results: int = 10,
        token_weight: float = 0.6,
        partial_weight: float = 0.4,
        min_score: int = 70,
    ) -> list[tuple[float, AddressMatch]]:
        """
        Search for addresses matching the query using weighted fuzzy matching.

        Args:
            query: Address query string
            max_results: Maximum number of results to return
            token_weight: Weight for token_set_ratio (0.0-1.0, default 0.6)
            partial_weight: Weight for partial_ratio (0.0-1.0, default 0.4)
            min_score: Minimum score threshold (0-100, default 70)

        Returns:
            List of (score, AddressMatch) tuples sorted by score descending
        """
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        postcode = extract_postcode_from_address(query)
        # Extract city from query (match text after last comma if it exists)
        city_from_query = None
        query_parts = query.rsplit(",", 1)
        if len(query_parts) == 2:
            potential_city = query_parts[1].strip().split()[-1]  # Get last word after comma
            # Remove postcode if it's there
            if postcode and postcode in potential_city:
                potential_city = query_parts[0].strip().rsplit(",", 1)[-1].strip()
            city_from_query = potential_city if potential_city else None

        # Query for scoring: just the street address part (without postcode and city)
        query_for_scoring = query.lower()
        # Remove postcode pattern from query
        if postcode:
            query_for_scoring = (
                query_for_scoring.replace(postcode.lower(), "").replace(",", " ").strip()
            )
        # Also try to remove city name if found
        if city_from_query:
            query_for_scoring = query_for_scoring.replace(city_from_query.lower(), "").strip()

        if not query_for_scoring.strip():
            return []

        # Adjust threshold for short queries (very lenient for short prefixes)
        effective_min_score = min_score
        if len(query_for_scoring.split()) == 1 and len(query_for_scoring) < 8:
            effective_min_score = max(60, min_score - 10)

        scored_results: list[tuple[float, AddressMatch]] = []

        if postcode:
            # Fast path: use postcode to narrow search, then fuzzy match street/housenumber
            rows = self.conn.execute(
                "SELECT street, housenumber, postcode, city, country "
                "FROM addresses "
                "WHERE postcode = ?",
                (postcode,),
            ).fetchall()

            for street, housenumber, pc, city, country in rows:
                # Score street + housenumber
                street_addr = f"{street}"
                if housenumber:
                    street_addr += f" {housenumber}"

                street_lower = street_addr.lower()
                token_score = fuzz.token_set_ratio(query_for_scoring, street_lower)
                partial_score = fuzz.partial_ratio(query_for_scoring, street_lower)
                street_score = token_weight * token_score + partial_weight * partial_score

                # Bonus: if city is in original query, boost score if it matches
                city_bonus = 0
                if city and city.lower() in query.lower():
                    city_bonus = 25

                total_score = street_score + city_bonus

                # Only include matches above threshold
                if total_score >= effective_min_score:
                    match = AddressMatch(
                        street=street,
                        housenumber=housenumber,
                        postcode=pc,
                        city=city,
                        country=country,
                    )
                    scored_results.append((total_score, match))

        else:
            # Slow path: search all addresses (limited to avoid memory issues)
            rows = self.conn.execute(
                "SELECT street, housenumber, postcode, city, country " "FROM addresses " "LIMIT ?",
                (max_results * 20,),
            ).fetchall()

            for street, housenumber, pc, city, country in rows:
                # Build address for fuzzy matching (street + housenumber only)
                full_addr = f"{street}"
                if housenumber:
                    full_addr += f" {housenumber}"
                if city:
                    full_addr += f", {city}"

                # Calculate weighted fuzzy match score (0-100)
                full_addr_lower = full_addr.lower()
                token_score = fuzz.token_set_ratio(query_for_scoring, full_addr_lower)
                partial_score = fuzz.partial_ratio(query_for_scoring, full_addr_lower)
                score = token_weight * token_score + partial_weight * partial_score

                # Only include matches above threshold
                if score >= effective_min_score:
                    match = AddressMatch(
                        street=street,
                        housenumber=housenumber,
                        postcode=pc,
                        city=city,
                        country=country,
                    )
                    scored_results.append((score, match))

        # Sort by score (descending), then by street name length (descending) as tiebreaker
        # Longer street names are preferred when scores are equal
        scored_results.sort(key=lambda x: (x[0], len(x[1].street or "")), reverse=True)
        return scored_results[:max_results]

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "AddressDB":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
