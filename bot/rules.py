"""Deterministic price, booking type, and Dubai location rules."""

from decimal import Decimal
import re
import unicodedata

from bot.parser import Booking


MIN_PRICE_EUR = Decimal("16")
OUTSIDE_DUBAI = re.compile(
    r"\b(?:sharjah|shj|abu dhabi|auh|ajman|fujairah|ras al khaimah|umm al quwain|al ain)\b",
)
DUBAI = re.compile(r"\b(?:dubai|dxb|jumeirah|deira)\b")


def normalize_location(location: str) -> str:
    """Normalize case, Unicode, and common separators for name matching."""
    value = unicodedata.normalize("NFKC", location).casefold()
    return " ".join(re.sub(r"[\s.,/\\\-–—]+", " ", value).split())


def is_dubai(location: str) -> bool:
    """Only recognize known Dubai names without an outside-emirate name."""
    value = normalize_location(location)
    return bool(DUBAI.search(value) and not OUTSIDE_DUBAI.search(value))


def rejection_reason(booking: Booking) -> str | None:
    """Return the first failed rule, or None if the booking qualifies."""
    if booking.booking_type != "accept":
        return "booking type is not Accept"
    if not booking.price_eur.is_finite() or booking.price_eur < MIN_PRICE_EUR:
        return "price is below €16 or invalid"
    if not is_dubai(booking.pickup):
        return "pickup is not confirmed in Dubai"
    if not is_dubai(booking.dropoff):
        return "drop-off is not confirmed in Dubai"
    return None


def should_accept(booking: Booking) -> bool:
    """Accept only explicit Accept bookings at or above €16 within Dubai."""
    return rejection_reason(booking) is None
