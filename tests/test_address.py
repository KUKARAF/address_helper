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


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_street_property(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test Address.street delegates to AddressMatch."""
    mock_match = AddressMatch(street="Hauptstraße")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    address = Address("Hauptstraße 1, Berlin")
    assert address.street == "Hauptstraße"


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_housenumber_property(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test Address.housenumber delegates to AddressMatch."""
    mock_match = AddressMatch(housenumber="42")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    address = Address("Hauptstraße 42, Berlin")
    assert address.housenumber == "42"


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_postcode_property(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test Address.postcode delegates to AddressMatch."""
    mock_match = AddressMatch(postcode="10115")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    address = Address("Hauptstraße 1, 10115 Berlin")
    assert address.postcode == "10115"


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_city_property(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test Address.city delegates to AddressMatch."""
    mock_match = AddressMatch(city="Berlin")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    address = Address("Hauptstraße 1, Berlin")
    assert address.city == "Berlin"


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_country_property(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test Address.country delegates to AddressMatch."""
    mock_match = AddressMatch(country="DE")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    address = Address("Hauptstraße 1, Berlin")
    assert address.country == "DE"


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_is_found_true(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test is_found returns True when match is complete."""
    mock_match = AddressMatch(street="Hauptstraße", city="Berlin")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    address = Address("Hauptstraße 1, Berlin")
    assert address.is_found is True


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_is_found_false_no_street(
    mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache
):
    """Test is_found returns False when street is missing."""
    mock_match = AddressMatch(city="Berlin")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    address = Address("Unknown, Berlin")
    assert address.is_found is False


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_is_found_false_no_match(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test is_found returns False when no match found."""
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = []
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    address = Address("Nonexistent Street, Nowhere")
    assert address.is_found is False


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_str(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test Address.__str__ delegates to AddressMatch."""
    mock_match = AddressMatch(street="Hauptstraße", housenumber="1", city="Berlin")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    address = Address("Hauptstraße 1, Berlin")
    assert "Hauptstraße" in str(address)
    assert "1" in str(address)
    assert "Berlin" in str(address)


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_repr(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test Address.__repr__ shows key fields."""
    mock_match = AddressMatch(street="Hauptstraße", city="Berlin", postcode="10115", country="DE")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    address = Address("Hauptstraße 1, 10115 Berlin")
    repr_str = repr(address)
    assert "Hauptstraße" in repr_str
    assert "Berlin" in repr_str


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_cache_reuse(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test _DB_CACHE reuses same DB for same iso_code."""
    mock_match = AddressMatch(street="Hauptstraße", city="Berlin")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    Address("Hauptstraße 1, Berlin", iso_code="DE")
    Address("Bahnhofstraße 2, Munich", iso_code="DE")

    # AddressDB should be instantiated only once for same iso_code
    assert mock_db_class.call_count == 1


@patch("address_standardizer.address.get_db_url")
@patch("address_standardizer.address.get_pbf_path")
@patch("address_standardizer.address.AddressDB")
def test_address_cache_separate_country(mock_db_class, mock_pbf_path, mock_db_url, clear_db_cache):
    """Test _DB_CACHE creates separate DBs for different iso_codes."""
    mock_match = AddressMatch(street="Some Street", city="Some City")
    mock_db_instance = MagicMock()
    mock_db_instance.search.return_value = [mock_match]
    mock_db_class.return_value = mock_db_instance
    mock_pbf_path.return_value = "/fake/path.pbf"
    mock_db_url.side_effect = ValueError("No URL")

    Address("Street 1, City", iso_code="DE")
    Address("Street 2, City", iso_code="AT")

    # AddressDB should be instantiated twice for different countries
    assert mock_db_class.call_count == 2
