"""Run the IWAY booking worker."""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from bot.listener import register_listener
from bot.telegram import authenticate, create_client, resolve_iway_chat
from config import load_settings


async def main() -> None:
    settings = load_settings()
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler("logs/bot.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"),
        ],
    )
    client = create_client(settings)
    try:
        await authenticate(client)
        chat = await resolve_iway_chat(client, settings.iway_chat)
        register_listener(client, chat, settings.dry_run)
        logging.info("Listening to IWAY chat; dry_run=%s", settings.dry_run)
        await client.run_until_disconnected()
        logging.warning("Telegram disconnected; worker stopped")
    except Exception:
        logging.exception("Telegram worker stopped after an error")
        raise
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
