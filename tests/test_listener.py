"""The listener is event driven and isolates failures between messages."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telethon import errors, events

from bot import listener


class FakeClient:
    def __init__(self):
        self.event = None
        self.handler = None
        self.disconnect = AsyncMock()

    def on(self, event):
        self.event = event

        def decorator(handler):
            self.handler = handler
            return handler

        return decorator


def test_listener_registers_for_one_incoming_chat(monkeypatch):
    client = FakeClient()
    expected_chat = object()
    captured = {}

    def fake_new_message(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(listener.events, "NewMessage", fake_new_message)
    listener.register_listener(client, expected_chat, dry_run=True)
    assert captured == {"chats": expected_chat, "incoming": True}
    assert client.handler is not None


def test_telethon_filter_rejects_other_chats_and_outgoing_messages():
    builder = events.NewMessage(chats=-1001234567890, incoming=True)
    builder.chats = {-1001234567890}
    builder.resolved = True

    def event(chat_id, outgoing=False):
        return SimpleNamespace(chat_id=chat_id, message=SimpleNamespace(out=outgoing))

    assert builder.filter(event(-1001234567890))
    assert not builder.filter(event(-1009999999999))
    assert not builder.filter(event(-1001234567890, outgoing=True))


def test_listener_processes_new_message(monkeypatch):
    client = FakeClient()
    process = AsyncMock()
    monkeypatch.setattr(listener, "process_booking", process)
    listener.register_listener(client, object(), dry_run=True)
    message = SimpleNamespace(id=123)
    asyncio.run(client.handler(SimpleNamespace(message=message)))
    process.assert_awaited_once_with(message, dry_run=True)


def test_listener_failure_does_not_escape_handler(monkeypatch):
    client = FakeClient()
    process = AsyncMock(side_effect=[RuntimeError("bad message"), None])
    monkeypatch.setattr(listener, "process_booking", process)
    listener.register_listener(client, object(), dry_run=True)
    asyncio.run(client.handler(SimpleNamespace(message=SimpleNamespace(id=123))))
    asyncio.run(client.handler(SimpleNamespace(message=SimpleNamespace(id=124))))
    assert process.await_count == 2


def test_invalid_session_disconnects_worker(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(listener, "process_booking", AsyncMock(side_effect=errors.AuthKeyUnregisteredError(None)))
    listener.register_listener(client, object(), dry_run=False)
    asyncio.run(client.handler(SimpleNamespace(message=SimpleNamespace(id=123))))
    client.disconnect.assert_awaited_once_with()
