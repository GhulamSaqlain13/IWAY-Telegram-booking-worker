"""Receive new messages from the configured IWAY chat."""

import logging

from telethon import errors, events

from bot.processor import process_booking


logger = logging.getLogger(__name__)


def register_listener(client, chat, dry_run: bool) -> None:
    """Subscribe to new incoming messages from the resolved IWAY chat only."""
    @client.on(events.NewMessage(chats=chat, incoming=True))
    async def on_new_message(event):
        try:
            await process_booking(event.message, dry_run=dry_run)
        except (errors.UnauthorizedError, errors.AuthKeyError):
            logger.critical("Telegram session is no longer authorized; stopping the worker", exc_info=True)
            await client.disconnect()
        except Exception:
            logger.exception("Failed to process message %s", event.message.id)
