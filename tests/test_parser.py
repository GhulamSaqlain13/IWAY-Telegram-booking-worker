from decimal import Decimal

from bot.parser import booking_type_from_message, parse_booking


MESSAGE = "On 1.10.2026 at 12.00 p.m.\nfrom Stella Di Mare Dubai Marina\nto Dubai Mall\n2 adults\nPrice: €22"


def test_parses_booking_with_accept_button():
    booking = parse_booking(MESSAGE, ["Accept"])
    assert booking.pickup == "Stella Di Mare Dubai Marina"
    assert booking.dropoff == "Dubai Mall"
    assert booking.price_eur == Decimal("22")
    assert booking.booking_type == "accept"


def test_parses_labeled_fields_and_decimal_eur():
    booking = parse_booking("Pickup: Dubai Airport\nDrop-off: Dubai Marina\nFare: 16,50 EUR", ["Accept"])
    assert booking.pickup == "Dubai Airport"
    assert booking.dropoff == "Dubai Marina"
    assert booking.price_eur == Decimal("16.50")


def test_ignores_offer_and_missing_accept():
    assert parse_booking(MESSAGE, ["Make an offer"]) is None
    assert parse_booking(MESSAGE, ["Accept", "Make an offer"]) is None
    assert parse_booking(MESSAGE, []) is None
    assert parse_booking(MESSAGE + "\nSuggest a price for the whole request", ["Accept"]) is None


def test_classifies_booking_action():
    assert booking_type_from_message(MESSAGE, ["Accept"]) == "accept"
    assert booking_type_from_message(MESSAGE, ["Make an offer"]) == "make_offer"
    assert booking_type_from_message(MESSAGE, ["Accept", "Make an offer"]) == "make_offer"
    assert booking_type_from_message(MESSAGE + "\nSuggest a price for the whole request", ["Accept"]) == "make_offer"
    assert booking_type_from_message(MESSAGE, ["Accept", "Accept"]) == "unknown"
    assert booking_type_from_message(MESSAGE, []) == "unknown"


def test_rejects_ambiguous_price():
    assert parse_booking(MESSAGE + "\nPrice: €30", ["Accept"]) is None


def test_rejects_missing_duplicate_and_multiline_fields():
    assert parse_booking("from\nto Dubai Mall\nPrice: €22", ["Accept"]) is None
    assert parse_booking(MESSAGE + "\nfrom DXB", ["Accept"]) is None
    assert parse_booking("from Dubai\nto\nPrice: €22", ["Accept"]) is None


def test_rejects_other_currency_and_malformed_price():
    assert parse_booking(MESSAGE.replace("€22", "22 USD"), ["Accept"]) is None
    assert parse_booking(MESSAGE.replace("€22", "€1,234.00"), ["Accept"]) is None
    assert parse_booking(MESSAGE.replace("€22", "€22.999"), ["Accept"]) is None


def test_unrelated_lines_do_not_count_as_fields():
    assert parse_booking("today\n" + MESSAGE, ["Accept"]) is not None
