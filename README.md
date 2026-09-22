# IWAY Telegram Automation Bot

Python 3.12+ worker that watches one IWAY Telegram chat and clicks an exact **Accept** button when the EUR price is at least 16 and both locations are confidently recognized as Dubai. Unknown or incomplete bookings are ignored.

## Required access and API credentials

- A Telegram **API ID** and **API hash** from [Telegram API development tools](https://my.telegram.org), entered as `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` in `.env`.
- A Telegram user account authorized to see the IWAY chat and use its Accept button. The first login needs that account's phone number, Telegram login code, and two-step password if enabled; Telethon then saves a local session.
- The IWAY chat username or numeric ID, entered as `IWAY_CHAT`. The account must already have access to that chat.

The worker uses Telegram's MTProto API through Telethon. It does not call an IWAY REST API, OpenAI API, or Telegram HTTP Bot API, and it does not require a bot token. Actual IWAY button behavior still needs to be checked with the authorized account.

## Offline preview

From PowerShell in `F:\iway-booking-bot`, run `& .\.venv\Scripts\python.exe preview.py`. This prints four sample decisions without credentials, a Telegram connection, or clicks. To preview an actual message, save its text as a UTF-8 file and run `& .\.venv\Scripts\python.exe preview.py --message-file .\sample.txt --button Accept`. Use `--button "Make an offer"` to preview an offer button. The preview shows the rules' decision; it cannot prove a live IWAY booking was accepted.

## Setup

1. Create a virtual environment: `python -m venv .venv` (or use an existing `.venv`).
2. Install dependencies into it: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` on Windows.
3. Copy `.env.example` to `.env` with `Copy-Item .env.example .env`, then add your Telegram API ID, API hash, and IWAY chat identifier. Keep `.env` and the session file private.
4. Run `.\.venv\Scripts\python.exe main.py` in an interactive Windows terminal. The first run prompts for your Telegram phone number, login code, and two-step verification password if enabled. Later runs reuse `data/iway.session`. The default `DRY_RUN=true` logs qualifying bookings without clicking.
5. After testing against an authorized IWAY account and confirming the actual button behavior, set `DRY_RUN=false` to enable clicks.

Run tests on Windows with `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`. Using the project interpreter avoids Windows app aliases for `python` and `py`. The cache flag avoids a permissions issue with this workspace's existing `.pytest_cache` directory.

## Telegram test channel

For a live integration check, use a separate authorized Telegram test group or channel and set `IWAY_CHAT` to it. Leave `DRY_RUN=true` first. Have a separate account or test bot post a message with separate `from`, `to`, and `Price:` lines and an exact `Accept` button; messages posted by the listening account itself are outgoing and ignored. Confirm that the log shows the parsed fields and a dry-run decision. Then post a price below €16, an outside-Dubai route, and a Make an offer button and confirm each is ignored. Only after confirming the button type and callback behavior in that test chat should you try `DRY_RUN=false` there. The real IWAY Accept behavior still requires validation in the authorized IWAY chat.

The listener subscribes to new incoming messages from the single resolved `IWAY_CHAT`. It processes each event as it arrives, logs ignored bookings, and catches errors per message so a malformed booking does not stop the worker.

`bot/processor.py` owns the per-message decision flow: parse the booking, evaluate the rules, then call the Accept action only when every rule passes. The listener only receives events and isolates processing errors; `main.py` starts the Telegram client and registers the listener.

The worker logs to the console and `logs/bot.log`. It records each message ID, parsed price and route, the decision, click attempts and responses, and errors. It does not log raw Telegram message text or Telegram credentials. The log rotates at 5 MB and keeps three backups; protect the log because pickup and drop-off names may contain customer trip details.

Telethon reconnects after transient disconnects. If it exhausts its retries, the process exits so a process manager can restart it. For a numeric `IWAY_CHAT`, the chat must appear in the signed-in account's dialogs. Use a username when available. Keep the session file private because it grants access to the Telegram account.

For safety, individual Accept requests have automatic retries and automatic flood-wait sleeps disabled. A rate limit, Telegram error, connection error, or missing button is logged and the booking is not retried automatically, since its final state may be uncertain. An invalid Telegram session stops the worker. Startup and disconnect errors are logged; restore the session or connection before restarting if needed.

## Parsing and safety limits

The parser expects separate `from`/`pickup`, `to`/`drop-off`, and `Price:`/`Fare:`/`Payout:` lines and an exact `Accept` button. It accepts `€22`, `22 €`, `22 EUR`, and decimal prices on the price line. Duplicate, missing, or malformed fields are ignored. Locations must contain a known Dubai name and no known outside-emirate name. Unknown locations are ignored; extend the location rules only after checking real IWAY samples. A successful Telegram button click is logged as a click attempt; whether IWAY completed the booking still needs validation with a real authorized session.

The rule accepts prices of €16.00 or more. It normalizes case and common punctuation in locations, then recognizes `Dubai`, `DXB`, `Jumeirah`, and `Deira` as Dubai markers. It rejects locations that also mention Sharjah (`SHJ`), Abu Dhabi (`AUH`), Ajman, Fujairah, Ras Al Khaimah, Umm Al Quwain, or Al Ain. Each ignored parsed booking logs the first failed rule. Actual IWAY location samples should be reviewed before live use.

The Accept action clicks only one exact `Accept` button of Telethon's normal text or inline callback type. URL, web view, duplicate, and mixed offer buttons are skipped. A returned Telegram response means the click request completed; it does not prove IWAY finalized the booking. Confirm the actual IWAY button type and resulting booking state with an authorized session before live operation.
