"""Main Address class for standardizing addresses."""

from typing import Optional

from .db import AddressDB
from .downloader import download_db
from .query import AddressMatch

# One AddressDB per iso_code, shared across all Address instances in a process
_DB_CACHE: dict[str, AddressDB] = {}


class Address:
    """
    Standardize an address string using OpenStreetMap data.

    Example:
        >>> addr = Address("Hauptstr 2a 56477 Rennerod")
        >>> print(addr.city)
        >>> print(addr.street)
    """

    def __init__(
        self,
        raw_string: str,
        iso_code: str = "DE",
        force_download: bool = False,
    ):
        """
        Initialize and standardize an address.

        Args:
            raw_string: Raw address string to standardize
            iso_code: ISO 3166-1 alpha-2 country code (default: "DE")
            force_download: Force re-download of the address database
        """
        self.raw_string = raw_string
        self.iso_code = iso_code

        iso_upper = iso_code.upper()
        if iso_upper not in _DB_CACHE:
            db_path = download_db(iso_code, force=force_download)
            _DB_CACHE[iso_upper] = AddressDB.from_path(db_path)

        db = _DB_CACHE[iso_upper]
        candidates = db.search(raw_string)

        # Store all candidates (score, match tuples)
        self._candidates: list[tuple[float, AddressMatch]] = candidates

        # Use the first match (best match)
        self._match: Optional[AddressMatch] = candidates[0][1] if candidates else None

        if not self._match:
            # Create empty match if no results found
            self._match = AddressMatch()

    @property
    def street(self) -> Optional[str]:
        """Street name."""
        return self._match.street if self._match else None

    @property
    def housenumber(self) -> Optional[str]:
        """House number."""
        return self._match.housenumber if self._match else None

    @property
    def postcode(self) -> Optional[str]:
        """Postal code."""
        return self._match.postcode if self._match else None

    @property
    def city(self) -> Optional[str]:
        """City name."""
        return self._match.city if self._match else None

    @property
    def country(self) -> Optional[str]:
        """Country."""
        return self._match.country if self._match else None

    @property
    def is_found(self) -> bool:
        """Whether a matching address was found."""
        return bool(self._match and self._match.is_complete())

    @property
    def candidates(self) -> list[tuple[float, AddressMatch]]:
        """All matching candidates with scores, sorted by score descending."""
        return self._candidates

    def __str__(self) -> str:
        """Format as standardized address string."""
        return str(self._match) if self._match else "Address not found"

    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"Address(street={self.street!r}, housenumber={self.housenumber!r}, "
            f"postcode={self.postcode!r}, city={self.city!r})"
        )
