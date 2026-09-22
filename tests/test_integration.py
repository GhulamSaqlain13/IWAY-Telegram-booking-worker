"""Offline Telegram event flow through listener, parser, rules, and action."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telethon.tl import types

from bot.listener import register_listener


IWAY_CHAT_ID = -1001234567890
OTHER_CHAT_ID = -1009999999999


class FakeTelegramClient:
    def __init__(self):
        self.builder = None
        self.handler = None

    def on(self, builder):
        self.builder = builder

        def register(handler):
            self.handler = handler
            return handler

        return register

    async def emit(self, message, chat_id=IWAY_CHAT_ID):
        event = SimpleNamespace(chat_id=chat_id, message=message)
        if self.builder.filter(event):
            await self.handler(event)


def fake_message(message_id, text, button_text="Accept"):
    click = AsyncMock(return_value=object())
    button = SimpleNamespace(
        text=button_text,
        button=SimpleNamespace(type=types.InlineButtonTypeCallback(data=b"accept")),
        click=click,
    )
    message = SimpleNamespace(
        id=message_id,
        chat_id=IWAY_CHAT_ID,
        out=False,
        raw_text=text,
        buttons=[[button]],
    )
    return message, click


def test_only_valid_new_iway_booking_clicks_accept():
    client = FakeTelegramClient()
    register_listener(client, IWAY_CHAT_ID, dry_run=False)
    client.builder.chats = {IWAY_CHAT_ID}
    client.builder.resolved = True

    valid, valid_click = fake_message(1, "from DXB\nto Dubai Marina\nPrice: €16")
    low_price, low_click = fake_message(2, "from DXB\nto Dubai Marina\nPrice: €15.50")
    outside, outside_click = fake_message(3, "from DXB\nto Sharjah\nPrice: €30")
    offer, offer_click = fake_message(4, "from DXB\nto Dubai Marina\nPrice: €30", "Make an offer")
    other_chat, other_chat_click = fake_message(5, "from DXB\nto Dubai Marina\nPrice: €30")

    async def deliver():
        for item in (valid, low_price, outside, offer):
            await client.emit(item)
        await client.emit(other_chat, chat_id=OTHER_CHAT_ID)

    asyncio.run(deliver())
    valid_click.assert_awaited_once_with()
    for click in (low_click, outside_click, offer_click, other_chat_click):
        click.assert_not_awaited()


def test_dry_run_never_clicks_valid_booking():
    client = FakeTelegramClient()
    register_listener(client, IWAY_CHAT_ID, dry_run=True)
    client.builder.chats = {IWAY_CHAT_ID}
    client.builder.resolved = True
    valid, click = fake_message(6, "from DXB\nto Dubai Marina\nPrice: €20")
    asyncio.run(client.emit(valid))
    click.assert_not_awaited()
