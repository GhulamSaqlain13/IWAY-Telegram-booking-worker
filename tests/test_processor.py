"""The decision engine forwards only qualifying bookings to the action."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot import processor


def message(message_id, text, label="Accept"):
    return SimpleNamespace(id=message_id, raw_text=text, buttons=[[SimpleNamespace(text=label)]])


def test_only_qualifying_message_reaches_action(monkeypatch):
    action = AsyncMock()
    monkeypatch.setattr(processor, "accept_booking", action)
    accepted = message(1, "from Dubai Airport\nto Dubai Marina\nPrice: €16")
    rejected = message(2, "from Dubai Airport\nto Sharjah\nPrice: €20")
    incomplete = message(3, "from Dubai Airport\nPrice: €50")

    asyncio.run(processor.process_booking(accepted, dry_run=True))
    asyncio.run(processor.process_booking(rejected, dry_run=True))
    asyncio.run(processor.process_booking(incomplete, dry_run=True))
    action.assert_awaited_once_with(accepted, dry_run=True)


def test_make_an_offer_never_reaches_action(monkeypatch):
    action = AsyncMock()
    monkeypatch.setattr(processor, "accept_booking", action)
    base_text = "from Dubai Airport\nto Dubai Marina\nPrice: €50"
    offer_button = message(4, base_text, label="Make an offer")
    offer_text = message(5, base_text + "\nSuggest a price for the whole request")

    asyncio.run(processor.process_booking(offer_button, dry_run=False))
    asyncio.run(processor.process_booking(offer_text, dry_run=False))
    action.assert_not_awaited()


def test_logs_received_parsed_and_decision_without_raw_message(monkeypatch, caplog):
    action = AsyncMock()
    monkeypatch.setattr(processor, "accept_booking", action)
    accepted = message(6, "from Dubai Airport\nto Dubai Marina\nPrice: €20\nPrivate note: secret-token")

    with caplog.at_level("INFO", logger="bot.processor"):
        asyncio.run(processor.process_booking(accepted, dry_run=True))

    assert "Booking message received" in caplog.text
    assert "price_eur=20" in caplog.text
    assert "pickup='Dubai Airport'" in caplog.text
    assert "dropoff='Dubai Marina'" in caplog.text
    assert "Decision QUALIFIED" in caplog.text
    assert "secret-token" not in caplog.text


def test_logs_ignore_reason(monkeypatch, caplog):
    monkeypatch.setattr(processor, "accept_booking", AsyncMock())
    rejected = message(7, "from Dubai Airport\nto Sharjah\nPrice: €20")
    with caplog.at_level("INFO", logger="bot.processor"):
        asyncio.run(processor.process_booking(rejected, dry_run=False))
    assert "Decision IGNORE" in caplog.text
    assert "drop-off is not confirmed in Dubai" in caplog.text
