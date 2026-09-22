from decimal import Decimal

import pytest

from bot.parser import Booking
from bot.rules import is_dubai, normalize_location, rejection_reason, should_accept


def booking(price="16", pickup="Dubai Airport", dropoff="Dubai Marina"):
    return Booking(pickup, dropoff, Decimal(price), "accept")


def test_price_boundary():
    assert should_accept(booking("16"))
    assert not should_accept(booking("15.50"))
    assert should_accept(booking("16.01"))
    assert not should_accept(booking("NaN"))
    assert not should_accept(booking("Infinity"))


def test_locations_fail_closed():
    assert is_dubai("DXB Terminal 3")
    assert is_dubai("Jumeirah")
    assert is_dubai("Deira")
    assert is_dubai("Bur Dubai")
    assert not should_accept(booking(dropoff="Sharjah"))
    assert not should_accept(booking(dropoff="Dubai to Abu Dhabi"))
    assert not should_accept(booking(dropoff="Dubai, Abu-Dhabi"))
    assert not should_accept(booking(dropoff="Dubai / Ras Al Khaimah"))
    assert not should_accept(booking(dropoff="Dubai — Abu Dhabi"))
    assert not should_accept(booking(dropoff="Dubai / AUH"))
    assert not should_accept(booking(dropoff="SHJ Airport"))
    assert not should_accept(booking(pickup="Unknown Hotel"))
    assert not is_dubai("DXB123")


def test_location_normalization():
    assert normalize_location("  DUBAI—Marina / Jumeirah ") == "dubai marina jumeirah"
    assert is_dubai("DUBAI—Marina")


def test_booking_type_must_be_accept():
    offer = Booking("Dubai Airport", "Dubai Marina", Decimal("30"), "make_offer")
    unknown = Booking("Dubai Airport", "Dubai Marina", Decimal("30"), "unknown")
    assert not should_accept(offer)
    assert not should_accept(unknown)


def test_rejection_reason_identifies_first_failed_rule():
    assert rejection_reason(booking()) is None
    assert rejection_reason(booking("15.99")) == "price is below €16 or invalid"
    assert rejection_reason(booking(pickup="Unknown Hotel")) == "pickup is not confirmed in Dubai"
    assert rejection_reason(booking(dropoff="Sharjah")) == "drop-off is not confirmed in Dubai"


@pytest.mark.parametrize(
    "location",
    ["Dubai Airport", "DXB", "Dubai Marina", "Downtown Dubai", "Jumeirah", "Deira", "Bur Dubai"],
)
def test_architecture_dubai_locations_work_for_pickup_and_dropoff(location):
    assert is_dubai(location)
    assert should_accept(booking(pickup=location))
    assert should_accept(booking(dropoff=location))


@pytest.mark.parametrize("location", ["Fujairah", "Sharjah", "Abu Dhabi", "Ajman"])
def test_architecture_outside_locations_reject_pickup_and_dropoff(location):
    assert not is_dubai(location)
    assert not should_accept(booking(pickup=location))
    assert not should_accept(booking(dropoff=location))


@pytest.mark.parametrize(
    ("pickup", "dropoff", "expected"),
    [
        ("Dubai", "Dubai", True),
        ("Dubai Airport", "Dubai Marina", True),
        ("Dubai Marina", "Jumeirah", True),
        ("Dubai", "Fujairah", False),
        ("Dubai", "Sharjah", False),
        ("Dubai", "Abu Dhabi", False),
    ],
)
def test_architecture_routes(pickup, dropoff, expected):
    assert should_accept(booking(pickup=pickup, dropoff=dropoff)) is expected
