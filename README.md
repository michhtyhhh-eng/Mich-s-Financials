# Finance & Market Telegram Bot

Tracks expenses, variable/commission income, and sends SGX + US market updates.
Weekly formatted report every Monday 9 AM SGT.

---

## Setup

### 1. Create Telegram Bot
1. Message @BotFather on Telegram → `/newbot`
2. Copy the **BOT_TOKEN**
3. Send any message to your new bot, then visit:
   `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
4. Copy your **chat id** from the `"id"` field in the response

### 2. Get Free Market API Key
1. Sign up at https://financialmodelingprep.com (free tier: 250 req/day)
2. Copy your **API key**

### 3. Customise Symbols (optional)
Edit `bot.py` lines near the top:
```python
US_SYMBOLS  = ["^GSPC", "^IXIC", "^DJI"]      # S&P 500, NASDAQ, Dow
SGX_SYMBOLS = ["D05.SI", "U11.SI", "Z74.SI"]  # DBS, UOB, SingTel
```
Add any SGX ticker with `.SI` suffix (e.g. `C6L.SI` for SIA).

### 4. Deploy on Railway
1. Push this folder to a GitHub repo
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Add these environment variables:
   ```
   BOT_TOKEN   = your telegram bot token
   CHAT_ID     = your telegram chat id
   FMP_API_KEY = your financialmodelingprep api key
   ```
4. Railway auto-detects the Procfile and runs `python bot.py`

---

## Commands

| Command | Example | Description |
|---|---|---|
| `/start` | `/start` | Show all commands |
| `/expense` | `/expense 45.50 food Lunch` | Log an expense |
| `/income` | `/income 800 commission AIA policy` | Log income |
| `/market` | `/market` | Live SGX + US snapshot |
| `/report` | `/report` | This week's table report |
| `/report month` | `/report month` | This month's report |
| `/list` | `/list` | Last 10 entries |
| `/delete` | `/delete` | Remove last entry (with confirm) |
| `/categories` | `/categories` | Monthly expense breakdown |

---

## Scheduled Messages

| Time | Message |
|---|---|
| Weekdays 8:30 AM SGT | Market update (SGX + US) |
| Monday 9:00 AM SGT | Weekly financial report |

---

## Income Types
Use any label you like — common examples:
- `salary` — fixed monthly
- `commission` — AIA / insurance sales
- `bonus` — performance or ad-hoc
- `freelance` — consulting income
- `rental` — property income

## Data Storage
Entries are saved in `data.json` in the same folder.
For persistent storage across Railway redeploys, consider upgrading to Supabase
(same pattern as your Diet Bot) — just swap `load()`/`save()` for Supabase calls.
