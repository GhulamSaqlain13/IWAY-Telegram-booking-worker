import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telethon import errors
from telethon.tl import types

from bot.actions import accept_booking, button_labels


def message(buttons):
    return SimpleNamespace(id=42, buttons=buttons)


def button(text="Accept", kind=None, response=object()):
    return SimpleNamespace(
        text=text,
        button=SimpleNamespace(type=kind or types.InlineButtonTypeCallback(data=b"accept")),
        click=AsyncMock(return_value=response),
    )


def test_button_labels_and_exact_match():
    accept = button()
    assert button_labels(message([[button("Details"), accept]])) == ["Details", "Accept"]
    assert not asyncio.run(accept_booking(message([[button("Accept now")]]), dry_run=False))


def test_dry_run_never_clicks():
    accept = button()
    assert not asyncio.run(accept_booking(message([[accept]]), dry_run=True))
    accept.click.assert_not_awaited()


def test_clicks_one_supported_accept_button():
    accept = button(kind=types.ButtonTypeDefault())
    assert asyncio.run(accept_booking(message([[accept]]), dry_run=False))
    accept.click.assert_awaited_once_with()


def test_rejects_duplicate_and_unsupported_buttons():
    first, second = button(), button()
    assert not asyncio.run(accept_booking(message([[first, second]]), dry_run=False))
    first.click.assert_not_awaited()
    second.click.assert_not_awaited()

    url = button(kind=types.InlineButtonTypeUrl(url="https://example.com"))
    assert not asyncio.run(accept_booking(message([[url]]), dry_run=False))
    url.click.assert_not_awaited()

    mixed = button()
    assert not asyncio.run(accept_booking(message([[mixed, button("Make an offer")]]), dry_run=False))
    mixed.click.assert_not_awaited()


def test_callback_without_response_is_not_reported_as_success():
    accept = button(response=None)
    assert not asyncio.run(accept_booking(message([[accept]]), dry_run=False))
    accept.click.assert_awaited_once_with()


def test_rate_limit_and_connection_error_do_not_retry(caplog):
    for failure in (errors.FloodWaitError(None, 30), OSError("disconnected")):
        accept = button()
        accept.click.side_effect = failure
        assert not asyncio.run(accept_booking(message([[accept]]), dry_run=False))
        accept.click.assert_awaited_once_with()
    assert "30 seconds" in caplog.text
    assert "outcome unknown" in caplog.text


def test_invalid_session_is_raised_for_worker_shutdown():
    accept = button()
    accept.click.side_effect = errors.AuthKeyUnregisteredError(None)
    try:
        asyncio.run(accept_booking(message([[accept]]), dry_run=False))
    except errors.UnauthorizedError:
        pass
    else:
        raise AssertionError("Invalid session should stop the worker")
