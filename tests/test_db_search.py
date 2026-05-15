from address_standardizer.query import AddressMatch


def test_db_search_fast_path_with_postcode(address_db):
    """Test search when postcode is found (uses indexed fast path)."""
    results = address_db.search("Hauptstraße 10115")
    assert len(results) > 0
    assert all(m.postcode == "10115" for _, m in results)
    assert all("hauptstraße" in m.street.lower() for _, m in results if m.street)


def test_db_search_slow_path_no_postcode(address_db):
    """Test search without postcode (full street scan)."""
    results = address_db.search("Bahnhofstraße")
    assert len(results) > 0
    assert all("bahnhofstraße" in m.street.lower() for _, m in results if m.street)


def test_db_search_no_results(address_db):
    """Test search with no matches."""
    results = address_db.search("Nonexistent Street")
    assert results == []


def test_db_search_max_results_default(address_db):
    """Test that search respects max_results parameter (default 10)."""
    # Markt appears in fixtures, Hauptstraße has 2 entries, Bahnhofstraße has 1
    # Add more rows to test the cap
    address_db.conn.executemany(
        "INSERT INTO addresses VALUES (?,?,?,?,?,?)",
        [("Markstraße", f"{i}", "10115", "Berlin", "DE", "markstraße") for i in range(1, 12)],
    )
    address_db.conn.commit()

    results = address_db.search("Markstraße 10115")
    assert len(results) == 10  # Default max_results


def test_db_search_max_results_custom(address_db):
    """Test custom max_results parameter."""
    address_db.conn.executemany(
        "INSERT INTO addresses VALUES (?,?,?,?,?,?)",
        [("Teststrasse", f"{i}", "10115", "Berlin", "DE", "teststrasse") for i in range(1, 8)],
    )
    address_db.conn.commit()

    results = address_db.search("Teststrasse 10115", max_results=3)
    assert len(results) <= 3


def test_db_search_returns_address_match(address_db):
    """Test that results are (score, AddressMatch) tuples."""
    results = address_db.search("Berlin")
    for score, match in results:
        assert isinstance(score, (int, float))
        assert isinstance(match, AddressMatch)


def test_db_search_partial_token_match(address_db):
    """Test fuzzy matching finds partial tokens."""
    # Hauptstraße with housenumber 1
    results = address_db.search("Haupt")
    # Should find rows where street contains "Hauptstraße"
    assert len(results) > 0
    assert any("Hauptstraße" in str(m) for _, m in results)
