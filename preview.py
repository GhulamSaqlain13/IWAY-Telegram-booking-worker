"""Show booking decisions offline without Telegram credentials or clicks."""

import argparse
from pathlib import Path

from bot.parser import booking_type_from_message, parse_booking
from bot.rules import rejection_reason


EXAMPLES = (
    ("Qualifying booking", "from Dubai Airport\nto Dubai Marina\nPrice: €22", ["Accept"]),
    ("Below minimum", "from Dubai Airport\nto Dubai Marina\nPrice: €15.50", ["Accept"]),
    ("Outside Dubai", "from Dubai Airport\nto Sharjah\nPrice: €30", ["Accept"]),
    ("Make an offer", "from Dubai Airport\nto Dubai Marina\nPrice: €50", ["Make an offer"]),
)


def preview_decision(text: str, labels: list[str]) -> str:
    """Describe the decision; this function never calls Telegram."""
    booking_type = booking_type_from_message(text, labels)
    if booking_type != "accept":
        return f"IGNORE: booking type is {booking_type}"
    booking = parse_booking(text, labels)
    if booking is None:
        return "IGNORE: booking fields are missing or ambiguous"
    reason = rejection_reason(booking)
    if reason is not None:
        return f"IGNORE: {reason.replace('€', 'EUR ')}"
    return "WOULD CLICK ACCEPT (dry preview only)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview IWAY booking decisions without Telegram access")
    parser.add_argument("--message-file", type=Path, help="UTF-8 file containing one IWAY message")
    parser.add_argument("--button", default="Accept", help="Button text shown with --message-file (default: Accept)")
    args = parser.parse_args()

    if args.message_file:
        text = args.message_file.read_text(encoding="utf-8")
        print(preview_decision(text, [args.button]))
        return

    for name, text, labels in EXAMPLES:
        print(f"{name}: {preview_decision(text, labels)}")


if __name__ == "__main__":
    main()
