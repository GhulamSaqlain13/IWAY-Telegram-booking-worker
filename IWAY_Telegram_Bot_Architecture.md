# **IWAY Telegram Automation Bot** 

Simplified Architecture & Module-by-Module Plan 

A lightweight Python + Telethon worker that watches the IWAY Telegram channel, parses incoming bookings, applies deterministic accept/ignore rules, and clicks Accept automatically — no backend, database, or dashboard required for V1. 

## **Overview** 

For the client's actual requirement, **no backend, FastAPI, PostgreSQL, dashboard, Redis, or frontend is needed.** This is essentially a **Python Telegram automation worker** . 

#### **Simplified Final Architecture** 



<!-- Start of picture text -->
                IWAY Telegram<br>                     |<br>                     v<br>              Python Automation<br>                     |<br>          +----------+----------+<br>          |                     |<br>       New Lead             Ignore<br>          |<br>          v<br>      Parse Message<br>          |<br>          v<br>     Check Rules<br>          |<br>     +----+----+<br>     |         |<br>   Valid     Invalid<br>     |         |<br>     v         v<br>  ACCEPT     IGNORE<br><!-- End of picture text -->

#### **Technology Stack** 

|**Technology**|**Purpose**|
|---|---|
|Python 3.12+|Main automation|
|Telethon|Connect to Telegram and monitor messages|
|asyncio|Real-time asynchronous processing|
|Regex|Extract price / locations / details|
|python-dotenv|Environment variables|
|logging|Logs / debugging|
|pytest|Testing|



## **What the Bot Actually Does** 

```
Telegram
   |
New IWAY message
   |
Read message
   |
Extract information
   |
Check price
   |
Check pickup
   |
Check drop-off
   |
Check Accept / Make Offer
   |
If valid -> Accept
Otherwise -> Ignore
```

No API server, no database (for V1), no website, and no dashboard are required. 

## **Recommended Project Structure** 

```
iway-bot/
|
+-- bot/
|   +-- telegram.py
|   +-- listener.py
|   +-- parser.py
|   +-- rules.py
|   +-- actions.py
|
+-- tests/
|   +-- test_parser.py
|   +-- test_rules.py
|
+-- config.py
+-- main.py
+-- .env
+-- .env.example
+-- requirements.txt
+-- README.md
```

### **MODULE 1 — Telegram Connection / Authentication** 

File: `telegram.py` 

Responsible only for: 

```
Connect to Telegram
Login
Maintain session
Reconnect
```

Implemented using **Telethon** . 

#### **Detailed responsibilities (from full module plan)** 

```
Create Telegram API credentials
Login
Create session
Store session securely
Reconnect automatically
```

### **MODULE 2 — Channel / Message Listener** 

File: `listener.py` 

Continuously watches the IWAY channel and reacts to new messages in real time. 

```
@client.on(events.NewMessage(chats=IWAY_CHANNEL))
async def new_lead(event):
```

```
    message = event.message
```

```
    # send message to parser
```

So whenever IWAY posts a **NEW BOOKING** , the bot receives it immediately. Polling (e.g. “check every 5 seconds”) is not necessary — the design is **event-based** for speed. 

#### **Detailed responsibilities** 

```
Monitor IWAY channel
Receive new messages instantly
Filter only relevant channel
```

### **MODULE 3 — Message Parser** 

File: `parser.py` 

Converts the raw Telegram message text into a structured Python object / dictionary. 

##### **Example input message:** 

```
On 1.10.2026 at 12.00 p.m.
from Stella Di Mare Dubai Marina
to Dubai Mall
```

```
2 adults
Price: €22
```

##### **Becomes:** 

```
{
    "pickup": "Stella Di Mare Dubai Marina",
    "dropoff": "Dubai Mall",
    "price": 22,
    "type": "accept"
}
```

The parser's only job: **Telegram text** → **structured booking data.** 

#### **Detailed responsibilities** 

```
Extract:
- pickup
- dropoff
- price
- booking type
```

### **MODULE 4 — Rules / Price & Location Validation** 

File: `rules.py` — the most important business logic. 

```
MIN_PRICE = 16
```

```
def should_accept(booking):
```

```
    if booking["type"] != "accept":
        return False
    if booking["price"] < 16:
        return False
    if not is_dubai(booking["pickup"]):
        return False
    if not is_dubai(booking["dropoff"]):
        return False
```

```
    return True
```

#### **Rule 1 — Price** 

Simple threshold: `price >= 16` 

|**Price**|**Result**|
|---|---|
|€10|Ignore|
|€15|Ignore|
|€15.50|Ignore|
|€16|Accept|
|€17|Accept|
|€30|Accept|
|€50|Accept|



The bot doesn't calculate the price — **it only reads the price already provided by IWAY.** 

#### **Rule 2 — “Make an Offer”** 

If the message says `Suggest a price for the whole request` or the button reads `Make an offer` , the bot does nothing: 

```
Make Offer
    |
  IGNORE
```

The bot **never** automatically enters a price. 

#### **Rule 3 — Pickup** 

Normalize the pickup location. Treated as **Dubai** : 

```
Dubai Airport
DXB
Dubai Marina
Downtown Dubai
Jumeirah
Deira
Bur Dubai
```

##### Treated as **outside Dubai** : 

```
Fujairah
Sharjah
Abu Dhabi
Ajman
```

#### **Rule 4 — Drop-off** 

Same normalization logic applied to the destination: 

```
Dubai -> Dubai                  OK
Dubai Airport -> Dubai Marina   OK
Dubai Marina -> Jumeirah        OK
Dubai -> Fujairah      X
Dubai -> Sharjah       X
Dubai -> Abu Dhabi     X
```

#### **Detailed responsibilities (Price & Location)** 

```
Price Validation:
Read IWAY price
Convert to number
Check >= 16 EUR
```

```
Location Validation:
Normalize pickup
Normalize drop-off
Determine Dubai / outside Dubai
Booking Type:
Accept
Make Offer
Unknown
```

### **MODULE 5 — Telegram Actions** 

File: `actions.py` — performs the actual Telegram interaction. 

##### **For a valid booking:** 

`VALID | Find "Accept" | Click Accept` **For an invalid booking:** `INVALID | Do nothing` 

##### **For an invalid booking:** 

This separation is useful because the rules module doesn't need to know anything about Telegram buttons. 

#### **Detailed responsibilities** 

```
Find Accept button
Click Accept
Record Telegram click response; verify final booking state with IWAY access
```

### **MODULE 6 — Decision Engine & Main Flow** 

`main.py` ties everything together and stays conceptually simple: 

```
async def process_booking(message):
```

```
    booking = parse_booking(message)
    if not booking:
        return
    if should_accept(booking):
```

```
        await accept_booking(message)
```

```
        print("Accept click sent; verify IWAY booking state")
```

```
    else:
```

```
        print("Booking ignored")
```

Decision logic: 

```
if:
```

```
    Accept type
    price >= 16
    pickup Dubai
    dropoff Dubai
```

```
-> ACCEPT
```

```
else:
```

```
-> IGNORE
```

#### **Complete Flow** 



<!-- Start of picture text -->
                    IWAY CHANNEL<br>                         |<br>                         v<br>                  New Message<br>                         |<br>                         v<br>                +----------------+<br>                |     Parser     |<br>                +-------+--------+<br>                        |<br>                        v<br>                 Booking Object<br>                        |<br>                        v<br>                +----------------+<br>                |     Rules      |<br>                +-------+--------+<br>                        |<br>            +-----------+-----------+<br>            |                       |<br>         INVALID                 VALID<br>            |                       |<br>            v                       v<br>          IGNORE               Accept Action<br>                                    |<br>                                    v<br>                             Click Accept<br><!-- End of picture text -->

### **MODULE 7 — Error Handling** 

Cases the automation must handle gracefully: 

```
Telegram disconnected
Button not found
```

```
Invalid message
Unknown price
Unknown location
Telegram rate limit
Session problem
```

### **MODULE 8 — Logging** 

A simple local log file is enough for V1 — no database required. 

```
logs/bot.log
```

##### Example entry: 

```
2026-09-21 18:50:10
BOOKING RECEIVED
Price: €20
Pickup: Dubai Airport
Dropoff: Dubai Marina
Decision: QUALIFIED; Accept click response received (IWAY state unverified)
```

What gets logged: 

```
New booking
Parsed data
Decision
Accept attempt
Accept click response/failure; final IWAY state requires separate verification
Errors
```

**Optional:** a small local file `processed.json` could prevent duplicate processing if needed — but should only be added if IWAY's behavior actually requires it. 

### **MODULE 9 — Testing** 

Files: `tests/test_parser.py` , `tests/test_rules.py` 

```
Parser tests
Price tests
Location tests
Rule tests
Fake Telegram messages
Telegram test channel
```

### **MODULE 10 — Deployment** 

```
VPS
Python environment
Environment variables
Run bot 24/7
Auto restart
Logs
```

For the first development version, this is enough: 

`Python | VPS/PC | python main.py` Docker is **optional** — useful for production, but not required for the bot's functionality. 

## **What the Project Does NOT Need (V1)** 

**Database (PostgreSQL)** — Not needed. A local log file (and optionally a small processed.json) is sufficient for the first version. 

**FastAPI / REST API** — Remove it. The Python process itself is the application — no API routes are required. 

**React / Next.js dashboard** — Remove it. No dashboard is required. 

**Redis** — Remove it. Not required. 

**Docker** — Optional. Not required for core functionality; useful later for production. 

**AI / ML decisioning** — Not required. The rules are fully deterministic (price threshold + pickup/drop-off in Dubai + booking type), so plain Python logic is faster and safer than an AI-based decision. 

Deterministic decision rule, restated: 

```
Price >= 16 EUR
AND
Pickup = Dubai
AND
Dropoff = Dubai
AND
Accept type
```

## **Final Technology Stack (V1)** 

```
+-------------------------------+
|       IWAY AUTOMATION          |
+-------------------------------+
|                                |
| Python 3.12+                   |
| Telethon                       |
| asyncio                        |
| Regex                          |
| python-dotenv                  |
| Python logging                 |
| pytest                         |
|                                |
+-------------------------------+
```

## **Key Takeaway** 

The client's actual product isn't a booking-management SaaS — it's a **Python automation that watches an IWAY Telegram channel and immediately accepts qualifying bookings.** The MVP core is: **Python + Telethon + parser + rules + Telegram action + logging.** 

**Open dependency to validate before committing to the client:** all filtering logic (parsing, price checks, location checks) can be built and tested without IWAY access, but the actual **Accept button click** must eventually be tested against an authorized IWAY Telegram account/session. 
