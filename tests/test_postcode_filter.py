from address_standardizer.postcode_filter import extract_postcode_from_address


def test_extract_postcode_from_address_simple():
    result = extract_postcode_from_address("Hauptstraße 1, 10115 Berlin")
    assert result == "10115"


def test_extract_postcode_from_address_beginning():
    result = extract_postcode_from_address("10115 Berlin")
    assert result == "10115"


def test_extract_postcode_from_address_end():
    result = extract_postcode_from_address("Berlin 10115")
    assert result == "10115"


def test_extract_postcode_from_address_none():
    result = extract_postcode_from_address("Berlin Germany")
    assert result is None


def test_extract_postcode_from_address_four_digit():
    result = extract_postcode_from_address("1234 Berlin")
    assert result is None


def test_extract_postcode_from_address_six_digit():
    result = extract_postcode_from_address("101234 Berlin")
    assert result is None


def test_extract_postcode_from_address_multiple_five_digit():
    result = extract_postcode_from_address("10115 Berlin or 80331 Munich")
    assert result == "10115"


def test_extract_postcode_from_address_word_boundary():
    result = extract_postcode_from_address("Street 12010115 Berlin")
    assert result is None
