import pytest

from address_standardizer.models import (
    COUNTRY_REGION_MAP,
    CountryRegion,
    RegionFile,
    get_country_region,
)


def test_country_region_map_loaded():
    assert COUNTRY_REGION_MAP is not None
    assert len(COUNTRY_REGION_MAP) > 0


def test_country_region_map_contains_de():
    assert "DE" in COUNTRY_REGION_MAP


def test_get_country_region_de():
    region = get_country_region("DE")
    assert isinstance(region, CountryRegion)
    assert region.iso_code == "DE"
    assert region.name == "Germany"
    assert region.full_file is not None
    assert region.preferred_file is not None


def test_get_country_region_case_insensitive():
    region_upper = get_country_region("DE")
    region_lower = get_country_region("de")
    assert region_upper.iso_code == region_lower.iso_code


def test_get_country_region_invalid():
    with pytest.raises(ValueError):
        get_country_region("XX")


def test_country_region_preferred_file_minified():
    region = get_country_region("DE")
    if region.minified_file is not None:
        assert region.preferred_file == region.minified_file


def test_country_region_preferred_file_fallback():
    # If minified is None, should use full_file
    # Create a test region with no minified file
    region = CountryRegion(
        iso_code="TEST",
        name="Test",
        full_file=RegionFile(
            url="http://example.com/test.pbf",
            checksum_url="http://example.com/test.md5",
            is_minified=False,
        ),
        minified_file=None,
        db_url=None,
        db_checksum=None,
    )
    assert region.preferred_file == region.full_file


def test_region_file_cache_filename():
    region = RegionFile(
        url="https://download.geofabrik.de/europe/germany-latest.osm.pbf",
        checksum_url="https://download.geofabrik.de/europe/germany-latest.osm.pbf.md5",
        is_minified=False,
    )
    assert region.cache_filename == "germany-latest.osm.pbf"


def test_region_file_cache_filename_path_with_query():
    region = RegionFile(
        url="https://example.com/path/to/file.pbf?v=1",
        checksum_url="http://example.com/file.md5",
        is_minified=False,
    )
    # cache_filename takes the last segment after splitting by /
    # Query params are included in the last segment
    assert region.cache_filename == "file.pbf?v=1"
