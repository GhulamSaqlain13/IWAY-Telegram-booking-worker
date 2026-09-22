"""Extract booking fields from a single IWAY Telegram message."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re


@dataclass(frozen=True)
class Booking:
    pickup: str
    dropoff: str
    price_eur: Decimal
    booking_type: str


PRICE_LABEL = re.compile(r"^(?:price|fare|payout)[ \t]*:", re.I)
PRICE_VALUE = re.compile(r"^[ \t]*(?:€[ \t]*)?([0-9]+(?:[.,][0-9]{1,2})?)[ \t]*(?:€|EUR)?[ \t]*$", re.I)
FROM_LABEL = re.compile(r"^(?:from|pickup)(?:[ \t]*:[ \t]*|[ \t]+)", re.I)
TO_LABEL = re.compile(r"^(?:to|drop[ -]?off)(?:[ \t]*:[ \t]*|[ \t]+)", re.I)
OFFER_TEXT = "suggest a price for the whole request"


def booking_type_from_message(text: str, button_labels: list[str]) -> str:
    """Classify the action shown by IWAY; ambiguous actions are never Accept."""
    labels = [label.strip().casefold() for label in button_labels if label]
    if OFFER_TEXT in text.casefold() or any("make an offer" in label for label in labels):
        return "make_offer"
    if labels.count("accept") == 1:
        return "accept"
    return "unknown"


def _value_for_label(lines: list[str], label: re.Pattern[str]) -> str | None:
    """Require exactly one nonempty, single-line value for a field."""
    values = [label.sub("", line, count=1).strip() for line in lines if label.match(line)]
    if len(values) != 1 or not values[0]:
        return None
    return " ".join(values[0].split())


def parse_booking(text: str, button_labels: list[str]) -> Booking | None:
    """Return a complete Accept booking, or None when fields or action are unsafe."""
    booking_type = booking_type_from_message(text, button_labels)
    if booking_type != "accept":
        return None

    lines = [line.strip() for line in text.splitlines()]
    pickup = _value_for_label(lines, FROM_LABEL)
    dropoff = _value_for_label(lines, TO_LABEL)
    price_lines = [PRICE_LABEL.sub("", line, count=1) for line in lines if PRICE_LABEL.match(line)]
    if pickup is None or dropoff is None or len(price_lines) != 1:
        return None
    match = PRICE_VALUE.fullmatch(price_lines[0])
    if match is None:
        return None
    try:
        price = Decimal(match.group(1).replace(",", "."))
    except InvalidOperation:
        return None
    return Booking(pickup, dropoff, price, booking_type)
