import sqlite3

import pytest

from address_standardizer.db import AddressDB


@pytest.fixture
def address_db(tmp_path):
    """SQLite-backed AddressDB fixture for testing search logic."""
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute(
        """CREATE TABLE addresses (
        street TEXT, housenumber TEXT, postcode TEXT,
        city TEXT, country TEXT, street_lower TEXT
    )"""
    )
    conn.executemany(
        "INSERT INTO addresses VALUES (?,?,?,?,?,?)",
        [
            ("Hauptstraße", "1", "10115", "Berlin", "DE", "hauptstraße"),
            ("Hauptstraße", "2", "10115", "Berlin", "DE", "hauptstraße"),
            ("Bahnhofstraße", "5", "80331", "München", "DE", "bahnhofstraße"),
            ("Markt", "10", "50667", "Köln", "DE", "markt"),
            ("Allee", "3", "12103", "Berlin", "DE", "allee"),
        ],
    )
    conn.commit()

    # Bypass AddressDB.__init__ to avoid filesystem/network I/O
    db = object.__new__(AddressDB)
    db.conn = conn
    yield db
    conn.close()
