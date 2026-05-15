from address_standardizer.query import AddressMatch


def test_address_match_complete():
    match = AddressMatch(
        street="Hauptstraße",
        housenumber="1",
        postcode="10115",
        city="Berlin",
        country="DE",
    )
    assert match.is_complete() is True


def test_address_match_incomplete_no_street():
    match = AddressMatch(
        street=None,
        housenumber="1",
        postcode="10115",
        city="Berlin",
        country="DE",
    )
    assert match.is_complete() is False


def test_address_match_incomplete_no_city():
    match = AddressMatch(
        street="Hauptstraße",
        housenumber="1",
        postcode="10115",
        city=None,
        country="DE",
    )
    assert match.is_complete() is False


def test_address_match_incomplete_both_missing():
    match = AddressMatch(street=None, housenumber="1", postcode="10115", city=None, country="DE")
    assert match.is_complete() is False


def test_address_match_str_full():
    match = AddressMatch(
        street="Hauptstraße",
        housenumber="1",
        postcode="10115",
        city="Berlin",
        country="DE",
    )
    assert str(match) == "Hauptstraße 1, 10115, Berlin, DE"


def test_address_match_str_omits_none():
    match = AddressMatch(
        street="Hauptstraße",
        housenumber=None,
        postcode="10115",
        city="Berlin",
        country=None,
    )
    assert str(match) == "Hauptstraße, 10115, Berlin"


def test_address_match_str_minimal():
    match = AddressMatch(street="Hauptstraße", city="Berlin")
    assert str(match) == "Hauptstraße, Berlin"


def test_address_match_str_all_none():
    match = AddressMatch()
    assert str(match) == ""
