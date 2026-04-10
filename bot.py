import os
import json
import logging
from datetime import datetime, timedelta
import pytz
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.environ["BOT_TOKEN"]
CHAT_ID     = os.environ["CHAT_ID"]        # your private chat ID (expenses/reports)
CHANNEL_ID  = os.environ["CHANNEL_ID"]    # e.g. @yourchannel or -100xxxxxxxxxx
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")
SGT         = pytz.timezone("Asia/Singapore")
DATA_FILE   = "data.json"

# ── Symbols ────────────────────────────────────────────────────────────────────
US_SYMBOLS = {
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ",
    "^DJI":  "Dow Jones",
}
SGX_SYMBOLS = {
    "D05.SI": "DBS",
    "U11.SI": "UOB",
    "Z74.SI": "SingTel",
}
# Macro context — shown as extra colour in the channel post
MACRO_SYMBOLS = {
    "^TNX": "US 10Y Yield",
    "GC=F": "Gold",
    "CL=F": "Crude Oil (WTI)",
}

# ── Data helpers ───────────────────────────────────────────────────────────────
def load() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"expenses": [], "income": []}

def save(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Market helpers ─────────────────────────────────────────────────────────────
def fetch_quote(symbol: str) -> dict | None:
    url = (
        f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
        f"?apikey={FMP_API_KEY}"
    )
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return data[0] if data else None
    except Exception as e:
        logger.error(f"Quote error {symbol}: {e}")
        return None

def sentiment_label(changes: list) -> tuple:
    """Return (emoji, label) based on list of % changes."""
    if not changes:
        return "➡️", "No Data"
    avg      = sum(changes) / len(changes)
    positives = sum(1 for c in changes if c > 0)
    ratio    = positives / len(changes)

    if avg >= 1.0 and ratio >= 0.7:
        return "🚀", "Strongly Bullish"
    elif avg >= 0.2 and ratio >= 0.5:
        return "📈", "Bullish"
    elif avg <= -1.0 and ratio <= 0.3:
        return "🔻", "Strongly Bearish"
    elif avg <= -0.2 and ratio <= 0.5:
        return "📉", "Bearish"
    else:
        return "➡️", "Mixed / Neutral"

def momentum_bar(chg: float) -> str:
    """5-block ASCII bar showing magnitude of move."""
    filled = min(int(abs(chg) / 0.5), 5)
    empty  = 5 - filled
    return ("▓" * filled + "░" * empty) if chg >= 0 else ("░" * empty + "▓" * filled)

def fmt_chg(chg: float) -> str:
    sign = "+" if chg >= 0 else ""
    return f"{sign}{chg:.2f}%"

# ── Channel post builder ───────────────────────────────────────────────────────
def build_channel_post() -> str:
    now  = datetime.now(SGT)
    date = now.strftime("%A, %d %b %Y")
    time = now.strftime("%H:%M SGT")

    lines = []
    lines.append("📊 *Daily Market Update*")
    lines.append(f"_{date} · {time}_\n")

    # US Markets
    lines.append("🇺🇸 *US MARKETS*")
    lines.append("```")
    lines.append(f"{'Index':<14} {'Price':>10}  {'Chg':>8}  Momentum")
    lines.append("─" * 48)
    us_changes = []
    for sym, name in US_SYMBOLS.items():
        q = fetch_quote(sym)
        if q:
            chg = q.get("changesPercentage", 0)
            us_changes.append(chg)
            lines.append(
                f"{name:<14} {q['price']:>10,.2f}  {fmt_chg(chg):>8}  {momentum_bar(chg)}"
            )
        else:
            lines.append(f"{name:<14} {'—':>10}  {'n/a':>8}")
    lines.append("```")
    if us_changes:
        emoji, label = sentiment_label(us_changes)
        lines.append(f"Sentiment: {emoji} *{label}*\n")

    # SGX Stocks
    lines.append("🇸🇬 *SGX STOCKS*")
    lines.append("```")
    lines.append(f"{'Stock':<14} {'Price':>10}  {'Chg':>8}  Momentum")
    lines.append("─" * 48)
    sgx_changes = []
    for sym, name in SGX_SYMBOLS.items():
        q = fetch_quote(sym)
        if q:
            chg = q.get("changesPercentage", 0)
            sgx_changes.append(chg)
            lines.append(
                f"{name:<14} SGD {q['price']:>6.3f}  {fmt_chg(chg):>8}  {momentum_bar(chg)}"
            )
        else:
            lines.append(f"{name:<14} {'—':>10}  {'n/a':>8}")
    lines.append("```")
    if sgx_changes:
        emoji, label = sentiment_label(sgx_changes)
        lines.append(f"Sentiment: {emoji} *{label}*\n")

    # Macro Context
    lines.append("🌐 *MACRO CONTEXT*")
    lines.append("```")
    lines.append(f"{'Asset':<22} {'Price':>8}  {'Chg':>8}")
    lines.append("─" * 42)
    for sym, name in MACRO_SYMBOLS.items():
        q = fetch_quote(sym)
        if q:
            chg   = q.get("changesPercentage", 0)
            price = q["price"]
            unit  = "%" if "Yield" in name else ""
            lines.append(f"{name:<22} {price:>8.2f}{unit}  {fmt_chg(chg):>8}")
        else:
            lines.append(f"{name:<22} {'—':>8}  {'n/a':>8}")
    lines.append("```")

    # Overall sentiment
    all_changes = us_changes + sgx_changes
    if all_changes:
        emoji, label = sentiment_label(all_changes)
        avg = sum(all_changes) / len(all_changes)
        lines.append(f"\n{'─' * 32}")
        lines.append("*Overall Market Sentiment*")
        lines.append(f"{emoji} *{label}*  _(avg: {fmt_chg(avg)})_")
        if "Strongly Bullish" in label:
            note = "Strong risk-on day. Broad gains across equities."
        elif "Bullish" in label:
            note = "Risk appetite is up. Equities broadly gaining."
        elif "Strongly Bearish" in label:
            note = "Heavy selling pressure. Risk-off across the board."
        elif "Bearish" in label:
            note = "Caution in markets. Watch for further downside."
        else:
            note = "Markets are mixed. No clear directional trend today."
        lines.append(f"_{note}_")

    lines.append(f"\n_Data: Financial Modeling Prep · {time}_")
    return "\n".join(lines)

# ── Quick snapshot (private chat /market) ─────────────────────────────────────
def build_quick_snapshot() -> str:
    now = datetime.now(SGT).strftime("%a, %d %b %Y %H:%M SGT")
    lines = [f"📊 *Market Snapshot* — {now}\n"]
    lines.append("🇺🇸 *US Markets*")
    for sym, name in US_SYMBOLS.items():
        q = fetch_quote(sym)
        if q:
            chg   = q.get("changesPercentage", 0)
            arrow = "🟢" if chg >= 0 else "🔴"
            lines.append(f"{arrow} {name}: `{q['price']:,.2f}` ({fmt_chg(chg)})")
        else:
            lines.append(f"⚠️ {name}: unavailable")
    lines.append("\n🇸🇬 *SGX*")
    for sym, name in SGX_SYMBOLS.items():
        q = fetch_quote(sym)
        if q:
            chg   = q.get("changesPercentage", 0)
            arrow = "🟢" if chg >= 0 else "🔴"
            lines.append(f"{arrow} {name}: `SGD {q['price']:.3f}` ({fmt_chg(chg)})")
        else:
            lines.append(f"⚠️ {name}: unavailable")
    return "\n".join(lines)

# ── Commands ───────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 *Finance & Market Bot*\n\n"
        "*Expenses*\n"
        "`/expense <amount> <category> [note]`\n"
        "e.g. `/expense 45.50 food Lunch at PS`\n\n"
        "*Income*\n"
        "`/income <amount> <type> [note]`\n"
        "e.g. `/income 800 commission AIA client`\n\n"
        "*Reports*\n"
        "`/report` — this week's summary\n"
        "`/report month` — this month's summary\n\n"
        "*Market*\n"
        "`/market` — quick snapshot\n"
        "`/marketfull` — full channel-style post with sentiment\n\n"
        "*Manage*\n"
        "`/list` — recent entries\n"
        "`/delete` — remove last entry\n"
        "`/categories` — expense breakdown"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_expense(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/expense <amount> <category> [note]`",
            parse_mode="Markdown"
        )
        return
    try:
        amount = float(args[0])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number.")
        return
    category = args[1].lower()
    note = " ".join(args[2:]) if len(args) > 2 else ""
    data = load()
    data["expenses"].append({
        "type": "expense", "amount": amount,
        "category": category, "note": note,
        "date": datetime.now(SGT).isoformat()
    })
    save(data)
    await update.message.reply_text(
        f"✅ Expense logged\n💸 SGD {amount:.2f} — *{category}*"
        f"{f' ({note})' if note else ''}",
        parse_mode="Markdown"
    )

async def cmd_income(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/income <amount> <type> [note]`",
            parse_mode="Markdown"
        )
        return
    try:
        amount = float(args[0])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number.")
        return
    income_type = args[1].lower()
    note = " ".join(args[2:]) if len(args) > 2 else ""
    data = load()
    data["income"].append({
        "type": "income", "amount": amount,
        "income_type": income_type, "note": note,
        "date": datetime.now(SGT).isoformat()
    })
    save(data)
    await update.message.reply_text(
        f"✅ Income logged\n💰 SGD {amount:.2f} — *{income_type}*"
        f"{f' ({note})' if note else ''}",
        parse_mode="Markdown"
    )

async def cmd_market(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Fetching...")
    await update.message.reply_text(build_quick_snapshot(), parse_mode="Markdown")

async def cmd_marketfull(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Building full market report...")
    await update.message.reply_text(build_channel_post(), parse_mode="Markdown")

async def cmd_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    period = ctx.args[0].lower() if ctx.args else "week"
    now = datetime.now(SGT)
    if period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = now.strftime("%B %Y")
    else:
        start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        label = f"Week of {start.strftime('%d %b')}"

    data = load()
    expenses  = [e for e in data["expenses"] if datetime.fromisoformat(e["date"]) >= start]
    incomes   = [i for i in data["income"]   if datetime.fromisoformat(i["date"]) >= start]
    total_exp = sum(e["amount"] for e in expenses)
    total_inc = sum(i["amount"] for i in incomes)
    net       = total_inc - total_exp

    cat_totals: dict = {}
    for e in expenses:
        cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
    inc_totals: dict = {}
    for i in incomes:
        inc_totals[i["income_type"]] = inc_totals.get(i["income_type"], 0) + i["amount"]

    lines = [f"📋 *Financial Report — {label}*\n"]
    lines.append("💰 *Income*\n```")
    lines.append(f"{'Type':<18} {'Amount':>10}")
    lines.append("─" * 30)
    for k, v in sorted(inc_totals.items(), key=lambda x: -x[1]):
        lines.append(f"{k.capitalize():<18} SGD {v:>8,.2f}")
    lines.append("─" * 30)
    lines.append(f"{'TOTAL':<18} SGD {total_inc:>8,.2f}\n```")
    lines.append("\n💸 *Expenses*\n```")
    lines.append(f"{'Category':<18} {'Amount':>10}  {'%':>5}")
    lines.append("─" * 35)
    for k, v in sorted(cat_totals.items(), key=lambda x: -x[1]):
        pct = (v / total_exp * 100) if total_exp else 0
        lines.append(f"{k.capitalize():<18} SGD {v:>8,.2f}  {pct:>4.0f}%")
    lines.append("─" * 35)
    lines.append(f"{'TOTAL':<18} SGD {total_exp:>8,.2f}\n```")
    net_emoji = "✅" if net >= 0 else "⚠️"
    lines.append(f"\n{net_emoji} *Net: SGD {net:+,.2f}*")
    if not expenses and not incomes:
        lines.append("\n_No entries found for this period._")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load()
    all_entries = sorted(
        data["expenses"] + data["income"],
        key=lambda x: x["date"], reverse=True
    )[:10]
    if not all_entries:
        await update.message.reply_text("No entries yet.")
        return
    lines = ["📝 *Last 10 entries*\n```"]
    lines.append(f"{'Date':<8} {'Type':<11} {'SGD':>8}")
    lines.append("─" * 30)
    for e in all_entries:
        dt   = datetime.fromisoformat(e["date"]).strftime("%d/%m")
        kind = e.get("category") or e.get("income_type") or "—"
        amt  = e["amount"]
        sign = "-" if "category" in e else "+"
        lines.append(f"{dt:<8} {kind[:11]:<11} {sign}{amt:>7,.2f}")
    lines.append("```")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_delete(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load()
    all_entries = sorted(
        [(i, e, "expenses") for i, e in enumerate(data["expenses"])] +
        [(i, e, "income")   for i, e in enumerate(data["income"])],
        key=lambda x: x[1]["date"], reverse=True
    )
    if not all_entries:
        await update.message.reply_text("Nothing to delete.")
        return
    idx, entry, source = all_entries[0]
    dt   = datetime.fromisoformat(entry["date"]).strftime("%d %b %H:%M")
    kind = entry.get("category") or entry.get("income_type")
    amt  = entry["amount"]
    keyboard = [[
        InlineKeyboardButton("✅ Yes, delete", callback_data=f"del:{source}:{idx}"),
        InlineKeyboardButton("❌ Cancel",       callback_data="del:cancel")
    ]]
    await update.message.reply_text(
        f"Delete last entry?\n💸 SGD {amt:.2f} — *{kind}* on {dt}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def cmd_categories(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data  = load()
    now   = datetime.now(SGT)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    expenses = [e for e in data["expenses"] if datetime.fromisoformat(e["date"]) >= start]
    total    = sum(e["amount"] for e in expenses)
    cat_totals: dict = {}
    for e in expenses:
        cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
    if not cat_totals:
        await update.message.reply_text("No expenses this month yet.")
        return
    lines = [f"📊 *Expense Categories — {now.strftime('%B')}*\n```"]
    lines.append(f"{'Category':<18} {'SGD':>8}  {'%':>5}")
    lines.append("─" * 34)
    for k, v in sorted(cat_totals.items(), key=lambda x: -x[1]):
        pct = v / total * 100
        bar = "█" * int(pct / 5)
        lines.append(f"{k.capitalize():<18} {v:>8,.2f}  {pct:>4.0f}% {bar}")
    lines.append("─" * 34)
    lines.append(f"{'TOTAL':<18} {total:>8,.2f}\n```")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ── Callbacks ──────────────────────────────────────────────────────────────────
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    if parts[0] == "del":
        if parts[1] == "cancel":
            await query.edit_message_text("❌ Cancelled.")
            return
        source, idx = parts[1], int(parts[2])
        data = load()
        removed = data[source].pop(idx)
        save(data)
        kind = removed.get("category") or removed.get("income_type")
        await query.edit_message_text(
            f"🗑 Deleted: SGD {removed['amount']:.2f} — {kind}"
        )

# ── Scheduled jobs ─────────────────────────────────────────────────────────────
async def scheduled_channel_update(app):
    """Mon–Sat 9:00 AM SGT → full market post to channel."""
    now = datetime.now(SGT)
    if now.weekday() == 6:   # skip Sunday only
        return
    logger.info("Posting daily market update to channel...")
    try:
        post = build_channel_post()
        await app.bot.send_message(
            chat_id=CHANNEL_ID,
            text=post,
            parse_mode="Markdown"
        )
        logger.info("Channel post sent successfully.")
    except Exception as e:
        logger.error(f"Channel post failed: {e}")

async def scheduled_weekly_report(app):
    """Every Monday 9:05 AM SGT → weekly financial report to private chat."""
    now   = datetime.now(SGT)
    start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    label = f"{start.strftime('%d %b')} – {(now - timedelta(days=1)).strftime('%d %b %Y')}"
    data  = load()

    expenses  = [e for e in data["expenses"] if datetime.fromisoformat(e["date"]) >= start]
    incomes   = [i for i in data["income"]   if datetime.fromisoformat(i["date"]) >= start]
    total_exp = sum(e["amount"] for e in expenses)
    total_inc = sum(i["amount"] for i in incomes)
    net       = total_inc - total_exp

    cat_totals: dict = {}
    for e in expenses:
        cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
    inc_totals: dict = {}
    for i in incomes:
        inc_totals[i["income_type"]] = inc_totals.get(i["income_type"], 0) + i["amount"]

    lines = [f"📋 *Weekly Report — {label}*\n"]
    lines.append("💰 *Income*\n```")
    lines.append(f"{'Type':<18} {'Amount':>10}")
    lines.append("─" * 30)
    for k, v in sorted(inc_totals.items(), key=lambda x: -x[1]):
        lines.append(f"{k.capitalize():<18} SGD {v:>8,.2f}")
    lines.append("─" * 30)
    lines.append(f"{'TOTAL':<18} SGD {total_inc:>8,.2f}\n```")
    lines.append("\n💸 *Expenses*\n```")
    lines.append(f"{'Category':<18} {'Amount':>10}  {'%':>5}")
    lines.append("─" * 35)
    for k, v in sorted(cat_totals.items(), key=lambda x: -x[1]):
        pct = (v / total_exp * 100) if total_exp else 0
        lines.append(f"{k.capitalize():<18} SGD {v:>8,.2f}  {pct:>4.0f}%")
    lines.append("─" * 35)
    lines.append(f"{'TOTAL':<18} SGD {total_exp:>8,.2f}\n```")
    net_emoji = "✅" if net >= 0 else "⚠️"
    lines.append(f"\n{net_emoji} *Net savings: SGD {net:+,.2f}*")
    if not expenses and not incomes:
        lines.append("\n_No entries this week._")

    await app.bot.send_message(chat_id=CHAT_ID, text="\n".join(lines), parse_mode="Markdown")

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("help",        cmd_start))
    app.add_handler(CommandHandler("expense",     cmd_expense))
    app.add_handler(CommandHandler("income",      cmd_income))
    app.add_handler(CommandHandler("market",      cmd_market))
    app.add_handler(CommandHandler("marketfull",  cmd_marketfull))
    app.add_handler(CommandHandler("report",      cmd_report))
    app.add_handler(CommandHandler("list",        cmd_list))
    app.add_handler(CommandHandler("delete",      cmd_delete))
    app.add_handler(CommandHandler("categories",  cmd_categories))
    app.add_handler(CallbackQueryHandler(callback_handler))

    scheduler = AsyncIOScheduler(timezone=SGT)
    # Mon–Sat 9:00 AM SGT — channel market post
    scheduler.add_job(
        scheduled_channel_update, "cron",
        day_of_week="mon-sat", hour=9, minute=0,
        args=[app]
    )
    # Every Monday 9:05 AM SGT — private weekly financial report
    scheduler.add_job(
        scheduled_weekly_report, "cron",
        day_of_week="mon", hour=9, minute=5,
        args=[app]
    )
    scheduler.start()

    logger.info("Bot started — channel updates Mon–Sat 9:00 AM SGT.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
