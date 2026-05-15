import pytest

from address_standardizer.downloader import get_db_url


def test_get_db_url_from_toml(monkeypatch):
    """Test get_db_url returns URL from links.toml when no override."""
    # Ensure env var is not set
    monkeypatch.delenv("DB_URL", raising=False)

    url = get_db_url("DE")
    assert url is not None
    assert "addresses.osm.db" in url or ".db" in url


def test_get_db_url_env_var_override(monkeypatch):
    """Test env var DB_URL takes precedence over toml."""
    custom_url = "http://custom-env.example.com/db.db"
    monkeypatch.setenv("DB_URL", custom_url)

    url = get_db_url("DE")
    assert url == custom_url


def test_get_db_url_param_override(monkeypatch):
    """Test parameter override_url takes precedence over env and toml."""
    custom_url = "http://custom-param.example.com/db.db"
    monkeypatch.delenv("DB_URL", raising=False)

    url = get_db_url("DE", override_url=custom_url)
    assert url == custom_url


def test_get_db_url_precedence_all_three(monkeypatch):
    """Test precedence: param > env var > toml."""
    env_url = "http://env.example.com/db.db"
    param_url = "http://param.example.com/db.db"
    monkeypatch.setenv("DB_URL", env_url)

    url = get_db_url("DE", override_url=param_url)
    assert url == param_url


def test_get_db_url_invalid_country():
    """Test get_db_url raises for unsupported country."""
    with pytest.raises(ValueError):
        get_db_url("XX")
