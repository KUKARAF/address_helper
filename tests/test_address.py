from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from address_standardizer import Address
from address_standardizer.address import _DB_CACHE
from address_standardizer.query import AddressMatch


@pytest.fixture
def clear_db_cache():
    """Clear the _DB_CACHE before and after each test."""
    _DB_CACHE.clear()
    yield
    _DB_CACHE.clear()


def _make_mocks(mock_db_class, mock_download_db, match):
    """Wire up standard mock plumbing for Address unit tests."""
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [(85.0, match)]
    mock_db_class.from_path.return_value = mock_db_instance
    mock_download_db.return_value = Path("/fake/DE-addresses.osm.db.v0.1.0")
    return mock_db_instance


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_street_property(mock_db_class, mock_download_db, clear_db_cache):
    """Test Address.street delegates to AddressMatch."""
    _make_mocks(mock_db_class, mock_download_db, AddressMatch(street="Hauptstraße"))
    assert Address("Hauptstraße 1, Berlin").street == "Hauptstraße"


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_housenumber_property(mock_db_class, mock_download_db, clear_db_cache):
    """Test Address.housenumber delegates to AddressMatch."""
    _make_mocks(mock_db_class, mock_download_db, AddressMatch(housenumber="42"))
    assert Address("Hauptstraße 42, Berlin").housenumber == "42"


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_postcode_property(mock_db_class, mock_download_db, clear_db_cache):
    """Test Address.postcode delegates to AddressMatch."""
    _make_mocks(mock_db_class, mock_download_db, AddressMatch(postcode="10115"))
    assert Address("Hauptstraße 1, 10115 Berlin").postcode == "10115"


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_city_property(mock_db_class, mock_download_db, clear_db_cache):
    """Test Address.city delegates to AddressMatch."""
    _make_mocks(mock_db_class, mock_download_db, AddressMatch(city="Berlin"))
    assert Address("Hauptstraße 1, Berlin").city == "Berlin"


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_country_property(mock_db_class, mock_download_db, clear_db_cache):
    """Test Address.country delegates to AddressMatch."""
    _make_mocks(mock_db_class, mock_download_db, AddressMatch(country="DE"))
    assert Address("Hauptstraße 1, Berlin").country == "DE"


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_is_found_true(mock_db_class, mock_download_db, clear_db_cache):
    """Test is_found returns True when match is complete."""
    _make_mocks(mock_db_class, mock_download_db, AddressMatch(street="Hauptstraße", city="Berlin"))
    assert Address("Hauptstraße 1, Berlin").is_found is True


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_is_found_false_no_street(mock_db_class, mock_download_db, clear_db_cache):
    """Test is_found returns False when street is missing."""
    _make_mocks(mock_db_class, mock_download_db, AddressMatch(city="Berlin"))
    assert Address("Unknown, Berlin").is_found is False


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_is_found_false_no_match(mock_db_class, mock_download_db, clear_db_cache):
    """Test is_found returns False when no match found."""
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = []
    mock_db_class.from_path.return_value = mock_db_instance
    mock_download_db.return_value = Path("/fake/DE-addresses.osm.db.v0.1.0")

    address = Address("Nonexistent Street, Nowhere")
    assert address.is_found is False
    assert address.candidates == []


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_str(mock_db_class, mock_download_db, clear_db_cache):
    """Test Address.__str__ delegates to AddressMatch."""
    _make_mocks(
        mock_db_class,
        mock_download_db,
        AddressMatch(street="Hauptstraße", housenumber="1", city="Berlin"),
    )
    result = str(Address("Hauptstraße 1, Berlin"))
    assert "Hauptstraße" in result
    assert "1" in result
    assert "Berlin" in result


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_repr(mock_db_class, mock_download_db, clear_db_cache):
    """Test Address.__repr__ shows key fields."""
    _make_mocks(
        mock_db_class,
        mock_download_db,
        AddressMatch(street="Hauptstraße", city="Berlin", postcode="10115", country="DE"),
    )
    repr_str = repr(Address("Hauptstraße 1, 10115 Berlin"))
    assert "Hauptstraße" in repr_str
    assert "Berlin" in repr_str


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_cache_reuse(mock_db_class, mock_download_db, clear_db_cache):
    """Test _DB_CACHE reuses same DB for same iso_code."""
    _make_mocks(
        mock_db_class,
        mock_download_db,
        AddressMatch(street="Hauptstraße", city="Berlin"),
    )
    Address("Hauptstraße 1, Berlin", iso_code="DE")
    Address("Bahnhofstraße 2, Munich", iso_code="DE")

    # from_path should be called only once for the same iso_code
    assert mock_db_class.from_path.call_count == 1


@patch("address_standardizer.address.download_db")
@patch("address_standardizer.address.AddressDB")
def test_address_cache_separate_country(mock_db_class, mock_download_db, clear_db_cache):
    """Test _DB_CACHE creates separate DBs for different iso_codes."""
    _make_mocks(
        mock_db_class,
        mock_download_db,
        AddressMatch(street="Some Street", city="Some City"),
    )
    Address("Street 1, City", iso_code="DE")
    Address("Street 2, City", iso_code="AT")

    # from_path should be called once per distinct iso_code
    assert mock_db_class.from_path.call_count == 2
