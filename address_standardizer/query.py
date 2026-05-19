"""Address match dataclass."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AddressMatch:
    """An address match found in the address database."""

    street: Optional[str] = None
    housenumber: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

    def __str__(self) -> str:
        """Format address as a single string."""
        parts = []
        if self.street and self.housenumber:
            parts.append(f"{self.street} {self.housenumber}")
        elif self.street:
            parts.append(self.street)
        if self.postcode:
            parts.append(self.postcode)
        if self.city:
            parts.append(self.city)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)

    def is_complete(self) -> bool:
        """Check if address has minimum required fields."""
        return bool(self.street and self.city)
