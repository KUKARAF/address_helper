"""SQLite-backed address index built from an OSM PBF file or downloaded from a remote URL."""

import sqlite3
from pathlib import Path
from typing import Any, Optional

import osmium
import requests

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
        conn.execute(
            "CREATE INDEX idx_postcode_street ON addresses(postcode, street_lower)"
        )
        conn.commit()
        conn.close()

        print(f"Index built at {self.db_path}", flush=True)

    def search(self, query: str, max_results: int = 10) -> list[AddressMatch]:
        """Search for addresses matching the query."""
        if self.conn is None:
            raise RuntimeError("Database connection not initialized")

        postcode = extract_postcode_from_address(query)
        query_lower = query.lower()
        query_tokens = [t.strip() for t in query_lower.split() if t.strip()]

        if not query_tokens:
            return []

        results: list[AddressMatch] = []

        if postcode:
            # Fast path: use postcode to narrow search
            for token in query_tokens:
                rows = self.conn.execute(
                    "SELECT street, housenumber, postcode, city, country "
                    "FROM addresses "
                    "WHERE postcode = ? AND street_lower LIKE ?",
                    (postcode, f"%{token}%"),
                ).fetchall()

                for street, housenumber, pc, city, country in rows:
                    match = AddressMatch(
                        street=street,
                        housenumber=housenumber,
                        postcode=pc,
                        city=city,
                        country=country,
                    )
                    results.append(match)
                    if len(results) >= max_results:
                        return results[:max_results]
        else:
            # Slow path: search by street tokens only
            seen = set()
            for token in query_tokens:
                rows = self.conn.execute(
                    "SELECT street, housenumber, postcode, city, country "
                    "FROM addresses "
                    "WHERE street_lower LIKE ? "
                    "LIMIT ?",
                    (f"%{token}%", max_results * 2),
                ).fetchall()

                for street, housenumber, pc, city, country in rows:
                    key = (street, housenumber, pc, city, country)
                    if key not in seen:
                        seen.add(key)
                        match = AddressMatch(
                            street=street,
                            housenumber=housenumber,
                            postcode=pc,
                            city=city,
                            country=country,
                        )
                        results.append(match)
                        if len(results) >= max_results:
                            return results[:max_results]

        return results

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "AddressDB":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
