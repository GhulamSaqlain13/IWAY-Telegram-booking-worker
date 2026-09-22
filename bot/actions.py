"""Telegram button interaction."""

import logging

from telethon import errors
from telethon.tl import types


logger = logging.getLogger(__name__)


def button_labels(message) -> list[str]:
    return [button.text for row in (message.buttons or []) for button in row]


async def accept_booking(message, dry_run: bool = True) -> bool:
    """Click one exact Accept button; return True only for a Telegram response.

    A response confirms the click request, not the final IWAY booking state.
    """
    buttons = [button for row in (message.buttons or []) for button in row]
    if any("make an offer" in button.text.strip().casefold() for button in buttons):
        logger.info("Skipping message %s with a Make an offer button", message.id)
        return False
    matches = [button for button in buttons if button.text.strip().casefold() == "accept"]
    if len(matches) != 1:
        logger.warning("Expected one Accept button, found %d", len(matches))
        return False
    button = matches[0]
    button_type = getattr(getattr(button, "button", None), "type", None)
    if not isinstance(button_type, (types.ButtonTypeDefault, types.InlineButtonTypeCallback)):
        logger.warning("Unsupported Accept button type %s for message %s", type(button_type).__name__, message.id)
        return False
    if dry_run:
        logger.info("DRY RUN: would click Accept for message %s", message.id)
        return False
    logger.info("Clicking Accept for message %s", message.id)
    try:
        response = await button.click()
    except errors.FloodWaitError as exc:
        logger.warning("Accept click for message %s hit Telegram rate limit (%s seconds); no retry", message.id, exc.seconds)
        return False
    except (errors.UnauthorizedError, errors.AuthKeyError):
        raise
    except errors.RPCError as exc:
        logger.error("Accept click for message %s failed with Telegram error %s; no retry", message.id, type(exc).__name__)
        return False
    except (OSError, TimeoutError) as exc:
        logger.error("Accept click for message %s had a connection error %s; outcome unknown, no retry", message.id, type(exc).__name__)
        return False
    if response is None:
        logger.warning("Accept click for message %s returned no response; outcome unknown", message.id)
        return False
    logger.info("Accept click received a Telegram response for message %s; confirm booking state in IWAY", message.id)
    return True
