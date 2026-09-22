"""Decision flow for one IWAY booking message."""

import logging

from bot.actions import accept_booking, button_labels
from bot.parser import parse_booking
from bot.rules import rejection_reason


logger = logging.getLogger(__name__)


async def process_booking(message, dry_run: bool) -> None:
    """Parse, evaluate, and attempt Accept only for qualifying bookings."""
    logger.info("Booking message received: chat_id=%s message_id=%s", getattr(message, "chat_id", None), message.id)
    booking = parse_booking(message.raw_text or "", button_labels(message))
    if booking is None:
        logger.info("Decision IGNORE message_id=%s: incomplete booking or no Accept option", message.id)
        return

    logger.info(
        "Booking parsed: message_id=%s price_eur=%s pickup=%r dropoff=%r type=%s",
        message.id,
        booking.price_eur,
        booking.pickup,
        booking.dropoff,
        booking.booking_type,
    )
    reason = rejection_reason(booking)
    if reason is not None:
        logger.info("Decision IGNORE message_id=%s: %s", message.id, reason)
        return

    logger.info("Decision QUALIFIED message_id=%s; dry_run=%s", message.id, dry_run)
    await accept_booking(message, dry_run=dry_run)
