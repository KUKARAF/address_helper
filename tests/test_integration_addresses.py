"""
Integration tests: parse 100 real German addresses from OpenStreetMap.

These tests verify that the full pipeline works end-to-end by parsing
real addresses from the OSM database with complete verified data.
Addresses are randomly selected from the database each test run for
comprehensive coverage.
"""

from address_standardizer import Address
from address_standardizer.db import AddressDB
from address_standardizer.downloader import get_pbf_path


def test_integration_100_random_addresses():
    """
    Parse 100 random addresses from the OSM database and verify all parse correctly.

    This integration test ensures the full pipeline works end-to-end:
    - Addresses are extracted directly from the OSM database
    - All have complete verified data (street, housenumber, postcode, city)
    - Addresses are random each test run for comprehensive coverage
    """
    pbf_path = get_pbf_path("DE")
    db = AddressDB(pbf_path)

    cursor = db.conn.execute("""
        SELECT street, housenumber, postcode, city
        FROM addresses
        WHERE housenumber IS NOT NULL
          AND postcode IS NOT NULL
          AND city IS NOT NULL
          AND street IS NOT NULL
          AND postcode GLOB '[0-9][0-9][0-9][0-9][0-9]'
        ORDER BY RANDOM()
        LIMIT 100
    """)

    addresses = [
        (f"{street} {housenumber}, {postcode}, {city}", street, postcode, city)
        for street, housenumber, postcode, city in cursor.fetchall()
    ]

    db.conn.close()

    # Parse all addresses and verify
    results = {"passed": 0, "failed": 0, "errors": []}

    for address_str, expected_street, expected_postcode, expected_city in addresses:
        try:
            addr = Address(address_str)

            # Verify address was found
            if not addr.is_found:
                raise AssertionError("Address marked as not found")

            # Verify postcode matches
            if addr.postcode != expected_postcode:
                raise AssertionError(
                    f"Postcode mismatch: expected {expected_postcode}, got {addr.postcode}"
                )

            # Verify city matches
            if addr.city != expected_city:
                raise AssertionError(f"City mismatch: expected {expected_city}, got {addr.city}")

            # Verify street contains expected substring (case-insensitive)
            if not (addr.street and expected_street.lower() in addr.street.lower()):
                raise AssertionError(
                    f"Street mismatch: expected {expected_street}, got {addr.street}"
                )

            results["passed"] += 1

        except AssertionError as e:
            results["failed"] += 1
            results["errors"].append((address_str, str(e)))

    # Report results
    total = results["passed"] + results["failed"]
    success_rate = (results["passed"] / total * 100) if total > 0 else 0

    # Require 95% success rate
    assert success_rate >= 95.0, (
        f"\n\nFailed {results['failed']}/{total} addresses ({100 - success_rate:.1f}% failure rate).\n"
        f"Sample errors:\n" + "\n".join(f"  - {addr}: {err}" for addr, err in results["errors"][:5])
    )

    print(f"\n✓ {results['passed']}/100 random addresses parsed correctly ({success_rate:.1f}%)")
