"""Extract postcode boundaries from PBF to enable postcode-based filtering."""

import re
from typing import Any, Optional

from .query import AddressMatch


class PostcodeExtractor:
    """Extract all postcodes from PBF and map to addresses."""

    def __init__(self):
        self.postcode_map: dict[str, list[AddressMatch]] = {}

    def node(self, n: Any) -> None:
        """Extract postcode from nodes."""
        if not n.tags:
            return

        tags = dict(n.tags)
        postcode = tags.get("addr:postcode")
        if not postcode:
            return

        match = AddressMatch(
            street=tags.get("addr:street"),
            housenumber=tags.get("addr:housenumber"),
            postcode=postcode,
            city=tags.get("addr:city"),
            country=tags.get("addr:country"),
        )

        # Store by postcode prefix (first 5 digits)
        pc_prefix = postcode[:5] if len(postcode) >= 5 else postcode
        if pc_prefix not in self.postcode_map:
            self.postcode_map[pc_prefix] = []
        self.postcode_map[pc_prefix].append(match)

    def way(self, w: Any) -> None:
        """Extract postcode from ways."""
        if not w.tags:
            return

        tags = dict(w.tags)
        postcode = tags.get("addr:postcode")
        if not postcode:
            return

        match = AddressMatch(
            street=tags.get("addr:street"),
            housenumber=tags.get("addr:housenumber"),
            postcode=postcode,
            city=tags.get("addr:city"),
            country=tags.get("addr:country"),
        )

        # Store by postcode prefix
        pc_prefix = postcode[:5] if len(postcode) >= 5 else postcode
        if pc_prefix not in self.postcode_map:
            self.postcode_map[pc_prefix] = []
        self.postcode_map[pc_prefix].append(match)


def extract_postcode_from_address(address_string: str) -> Optional[str]:
    """Try to extract a postcode from the address string.

    Matches: German (5 digits), Dutch (4 digits + 2 letters), and other formats.
    """
    # Try German format first (5 digits)
    match = re.search(r"\b\d{5}\b", address_string)
    if match:
        return match.group()

    # Try Dutch format (4 digits + 2 letters, e.g. 7534XJ)
    match = re.search(r"\b\d{4}[A-Z]{2}\b", address_string, re.IGNORECASE)
    if match:
        return match.group()

    return None
