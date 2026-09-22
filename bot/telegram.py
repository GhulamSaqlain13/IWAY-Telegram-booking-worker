"""Telegram login, session reuse, and IWAY chat resolution."""

import logging

from telethon import TelegramClient

from config import Settings


logger = logging.getLogger(__name__)


def create_client(settings: Settings) -> TelegramClient:
    return TelegramClient(
        str(settings.session_path),
        settings.api_id,
        settings.api_hash,
        auto_reconnect=True,
        connection_retries=10,
        retry_delay=5,
        request_retries=0,
        flood_sleep_threshold=0,
    )


async def authenticate(client: TelegramClient) -> None:
    """Reuse a saved session or prompt for phone, code, and 2FA on first run."""
    await client.start()
    account = await client.get_me()
    if account is None:
        raise RuntimeError("Telegram login did not return an authorized account")
    logger.info("Telegram authenticated as account %s", account.id)


async def resolve_iway_chat(client: TelegramClient, identifier: str):
    """Resolve a username or a numeric ID belonging to an accessible dialog."""
    identifier = identifier.strip()
    if not identifier:
        raise ValueError("IWAY_CHAT cannot be empty")
    if identifier.lstrip("-").isdigit():
        chat_id = int(identifier)
        for dialog in await client.get_dialogs():
            if dialog.id == chat_id or dialog.entity.id == chat_id:
                return dialog.entity
        raise ValueError(f"IWAY_CHAT {identifier} was not found in this account's dialogs")
    return await client.get_entity(identifier)
