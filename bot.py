import os
import json
import logging
from datetime import datetime, timedelta
import pytz
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.environ["BOT_TOKEN"]
CHAT_ID     = os.environ["CHAT_ID"]
CHANNEL_ID  = os.environ["CHANNEL_ID"]
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")
SGT         = pytz.timezone("Asia/Singapore")
DATA_FILE   = "data.json"

# ── Conversation states ────────────────────────────────────────────────────────
WAITING_EXPENSE = 1
WAITING_INCOME  = 2

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
MACRO_SYMBOLS = {
    "^TNX": "US 10Y Yield",
    "GC=F": "Gold",
    "CL=F": "Crude Oil (WTI)",
}

# ── Keyboards ──────────────────────────────────────────────────────────────────
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📈 Market Snapshot",  "📊 Full Market Report"],
        ["💸 Log Expense",      "💰 Log Income"],
        ["📋 Weekly Report",    "📅 Monthly Report"],
        ["🗂 Categories",       "📝 Recent Entries"],
        ["🗑 Delete Last Entry", "ℹ️ Help"],
    ],
    resize_keyboard=True,
    persistent=True
)

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
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return data[0] if data else None
    except Exception as e:
        logger.error(f"Quote error {symbol}: {e}")
        return None

def fmt_chg(chg: float) -> str:
    sign = "+" if chg >= 0 else ""
    return f"{sign}{chg:.2f}%"

def momentum_bar(chg: float) -> str:
    filled = min(int(abs(chg) / 0.5), 5)
    empty  = 5 - filled
    return ("▓" * filled + "░" * empty) if chg >= 0 else ("░" * empty + "▓" * filled)

def sentiment_label(changes: list) -> tuple:
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

def build_quick_snapshot() -> str:
    now = datetime.now(SGT).strftime("%a, %d %b %Y %H:%M SGT")
    lines = [f"📈 *Market Snapshot*\n_{now}_\n"]
    lines.append("🇺🇸 *US Markets*")
    for sym, name in US_SYMBOLS.items():
        q = fetch_quote(sym)
        if q:
            chg = q.get("changesPercentage", 0)
            arrow = "🟢" if chg >= 0 else "🔴"
            lines.append(f"{arrow} {name}: `{q['price']:,.2f}` ({fmt_chg(chg)})")
        else:
            lines.append(f"⚠️ {name}: unavailable")
    lines.append("\n🇸🇬 *SGX*")
    for sym, name in SGX_SYMBOLS.items():
        q = fetch_quote(sym)
        if q:
            chg = q.get("changesPercentage", 0)
            arrow = "🟢" if chg >= 0 else "🔴"
            lines.append(f"{arrow} {name}: `SGD {q['price']:.3f}` ({fmt_chg(chg)})")
        else:
            lines.append(f"⚠️ {name}: unavailable")
    return "\n".join(lines)

def build_channel_post() -> str:
    now  = datetime.now(SGT)
    date = now.strftime("%A, %d %b %Y")
    time = now.strftime("%H:%M SGT")
    lines = []
    lines.append("📊 *Daily Market Update*")
    lines.append(f"_{date} · {time}_\n")

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
            lines.append(f"{name:<14} {q['price']:>10,.2f}  {fmt_chg(chg):>8}  {momentum_bar(chg)}")
        else:
            lines.append(f"{name:<14} {'—':>10}  {'n/a':>8}")
    lines.append("```")
    if us_changes:
        emoji, label = sentiment_label(us_changes)
        lines.append(f"Sentiment: {emoji} *{label}*\n")

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
            lines.append(f"{name:<14} SGD {q['price']:>6.3f}  {fmt_chg(chg):>8}  {momentum_bar(chg)}")
        else:
            lines.append(f"{name:<14} {'—':>10}  {'n/a':>8}")
    lines.append("```")
    if sgx_changes:
        emoji, label = sentiment_label(sgx_changes)
        lines.append(f"Sentiment: {emoji} *{label}*\n")

    lines.append("🌐 *MACRO CONTEXT*")
    lines.append("```")
    lines.append(f"{'Asset':<22} {'Price':>8}  {'Chg':>8}")
    lines.append("─" * 42)
    for sym, name in MACRO_SYMBOLS.items():
        q = fetch_quote(sym)
        if q:
            chg  = q.get("changesPercentage", 0)
            unit = "%" if "Yield" in name else ""
            lines.append(f"{name:<22} {q['price']:>8.2f}{unit}  {fmt_chg(chg):>8}")
        else:
            lines.append(f"{name:<22} {'—':>8}  {'n/a':>8}")
    lines.append("```")

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

# ── Report builders ────────────────────────────────────────────────────────────
def build_report(period: str) -> str:
    now = datetime.now(SGT)
    if period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = now.strftime("%B %Y")
    else:
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
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
    return "\n".join(lines)

# ── Handlers ───────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to Mich's Finance Bot!*\n\n"
        "Track your expenses, income, and get daily market updates.\n\n"
        "Use the buttons below to get started 👇",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD
    )

async def show_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *How to use this bot*\n\n"
        "📈 *Market Snapshot* — quick SGX + US prices\n"
        "📊 *Full Market Report* — detailed post with sentiment\n\n"
        "💸 *Log Expense* — tap and follow the prompt\n"
        "💰 *Log Income* — tap and follow the prompt\n\n"
        "📋 *Weekly Report* — this week's income vs expenses\n"
        "📅 *Monthly Report* — this month's breakdown\n\n"
        "🗂 *Categories* — monthly spend by category\n"
        "📝 *Recent Entries* — last 10 transactions\n"
        "🗑 *Delete Last Entry* — removes most recent entry\n\n"
        "_Channel gets daily market updates Mon–Sat at 9 AM SGT_ 📡",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD
    )

# ── Expense conversation ───────────────────────────────────────────────────────
async def expense_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💸 *Log Expense*\n\n"
        "Send me the details in this format:\n"
        "`amount category note`\n\n"
        "Examples:\n"
        "`45.50 food Chicken rice at Maxwell`\n"
        "`120 transport Grab to airport`\n"
        "`89.90 shopping NTUC groceries`\n\n"
        "_Type /cancel to go back_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_EXPENSE

async def expense_receive(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "/cancel":
        await update.message.reply_text("❌ Cancelled.", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END
    parts = text.split(None, 2)
    if len(parts) < 2:
        await update.message.reply_text(
            "⚠️ Please send: `amount category note`\ne.g. `45.50 food Lunch`",
            parse_mode="Markdown"
        )
        return WAITING_EXPENSE
    try:
        amount = float(parts[0])
    except ValueError:
        await update.message.reply_text("⚠️ First value must be a number. Try again:")
        return WAITING_EXPENSE
    category = parts[1].lower()
    note     = parts[2] if len(parts) > 2 else ""
    data = load()
    data["expenses"].append({
        "type": "expense", "amount": amount,
        "category": category, "note": note,
        "date": datetime.now(SGT).isoformat()
    })
    save(data)
    await update.message.reply_text(
        f"✅ *Expense logged!*\n\n"
        f"💸 SGD {amount:.2f}\n"
        f"🏷 Category: *{category.capitalize()}*"
        f"{f'{chr(10)}📝 Note: {note}' if note else ''}",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD
    )
    return ConversationHandler.END

# ── Income conversation ────────────────────────────────────────────────────────
async def income_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 *Log Income*\n\n"
        "Send me the details in this format:\n"
        "`amount type note`\n\n"
        "Examples:\n"
        "`3200 salary March salary`\n"
        "`800 commission AIA policy — client name`\n"
        "`500 bonus performance bonus`\n\n"
        "_Type /cancel to go back_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_INCOME

async def income_receive(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "/cancel":
        await update.message.reply_text("❌ Cancelled.", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END
    parts = text.split(None, 2)
    if len(parts) < 2:
        await update.message.reply_text(
            "⚠️ Please send: `amount type note`\ne.g. `800 commission AIA policy`",
            parse_mode="Markdown"
        )
        return WAITING_INCOME
    try:
        amount = float(parts[0])
    except ValueError:
        await update.message.reply_text("⚠️ First value must be a number. Try again:")
        return WAITING_INCOME
    income_type = parts[1].lower()
    note        = parts[2] if len(parts) > 2 else ""
    data = load()
    data["income"].append({
        "type": "income", "amount": amount,
        "income_type": income_type, "note": note,
        "date": datetime.now(SGT).isoformat()
    })
    save(data)
    await update.message.reply_text(
        f"✅ *Income logged!*\n\n"
        f"💰 SGD {amount:.2f}\n"
        f"🏷 Type: *{income_type.capitalize()}*"
        f"{f'{chr(10)}📝 Note: {note}' if note else ''}",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD
    )
    return ConversationHandler.END

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

# ── Button handler ─────────────────────────────────────────────────────────────
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📈 Market Snapshot":
        await update.message.reply_text("⏳ Fetching market data...", reply_markup=MAIN_KEYBOARD)
        await update.message.reply_text(build_quick_snapshot(), parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)

    elif text == "📊 Full Market Report":
        await update.message.reply_text("⏳ Building full report...", reply_markup=MAIN_KEYBOARD)
        await update.message.reply_text(build_channel_post(), parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)

    elif text == "📋 Weekly Report":
        await update.message.reply_text(build_report("week"), parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)

    elif text == "📅 Monthly Report":
        await update.message.reply_text(build_report("month"), parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)

    elif text == "🗂 Categories":
        data  = load()
        now   = datetime.now(SGT)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        expenses = [e for e in data["expenses"] if datetime.fromisoformat(e["date"]) >= start]
        total    = sum(e["amount"] for e in expenses)
        cat_totals: dict = {}
        for e in expenses:
            cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
        if not cat_totals:
            await update.message.reply_text("No expenses this month yet.", reply_markup=MAIN_KEYBOARD)
            return
        lines = [f"🗂 *Expense Categories — {now.strftime('%B')}*\n```"]
        lines.append(f"{'Category':<18} {'SGD':>8}  {'%':>5}")
        lines.append("─" * 34)
        for k, v in sorted(cat_totals.items(), key=lambda x: -x[1]):
            pct = v / total * 100
            bar = "█" * int(pct / 5)
            lines.append(f"{k.capitalize():<18} {v:>8,.2f}  {pct:>4.0f}% {bar}")
        lines.append("─" * 34)
        lines.append(f"{'TOTAL':<18} {total:>8,.2f}\n```")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)

    elif text == "📝 Recent Entries":
        data = load()
        all_entries = sorted(
            data["expenses"] + data["income"],
            key=lambda x: x["date"], reverse=True
        )[:10]
        if not all_entries:
            await update.message.reply_text("No entries yet.", reply_markup=MAIN_KEYBOARD)
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
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)

    elif text == "🗑 Delete Last Entry":
        data = load()
        all_entries = sorted(
            [(i, e, "expenses") for i, e in enumerate(data["expenses"])] +
            [(i, e, "income")   for i, e in enumerate(data["income"])],
            key=lambda x: x[1]["date"], reverse=True
        )
        if not all_entries:
            await update.message.reply_text("Nothing to delete.", reply_markup=MAIN_KEYBOARD)
            return
        idx, entry, source = all_entries[0]
        kind = entry.get("category") or entry.get("income_type")
        amt  = entry["amount"]
        dt   = datetime.fromisoformat(entry["date"]).strftime("%d %b %H:%M")
        # Store pending delete in user context
        ctx.user_data["pending_delete"] = {"source": source, "idx": idx}
        confirm_kb = ReplyKeyboardMarkup(
            [["✅ Yes, delete it", "❌ Cancel"]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text(
            f"🗑 Delete this entry?\n\n"
            f"💸 SGD {amt:.2f} — *{kind}*\n"
            f"📅 {dt}",
            parse_mode="Markdown",
            reply_markup=confirm_kb
        )

    elif text == "✅ Yes, delete it":
        pending = ctx.user_data.get("pending_delete")
        if pending:
            data = load()
            removed = data[pending["source"]].pop(pending["idx"])
            save(data)
            kind = removed.get("category") or removed.get("income_type")
            await update.message.reply_text(
                f"🗑 Deleted: SGD {removed['amount']:.2f} — {kind}",
                reply_markup=MAIN_KEYBOARD
            )
            ctx.user_data.pop("pending_delete", None)
        else:
            await update.message.reply_text("Nothing to delete.", reply_markup=MAIN_KEYBOARD)

    elif text == "❌ Cancel":
        ctx.user_data.pop("pending_delete", None)
        await update.message.reply_text("❌ Cancelled.", reply_markup=MAIN_KEYBOARD)

    elif text == "ℹ️ Help":
        await show_help(update, ctx)

# ── Scheduled jobs ─────────────────────────────────────────────────────────────
async def scheduled_channel_update(app):
    now = datetime.now(SGT)
    if now.weekday() == 6:
        return
    logger.info("Posting daily market update to channel...")
    try:
        await app.bot.send_message(
            chat_id=CHANNEL_ID,
            text=build_channel_post(),
            parse_mode="Markdown"
        )
        logger.info("Channel post sent.")
    except Exception as e:
        logger.error(f"Channel post failed: {e}")

async def scheduled_weekly_report(app):
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

    # Expense conversation
    expense_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💸 Log Expense$"), expense_start)],
        states={WAITING_EXPENSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_receive)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Income conversation
    income_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Log Income$"), income_start)],
        states={WAITING_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_receive)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_start))
    app.add_handler(expense_conv)
    app.add_handler(income_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))

    scheduler = AsyncIOScheduler(timezone=SGT)
    scheduler.add_job(scheduled_channel_update, "cron", day_of_week="mon-sat", hour=9, minute=0,  args=[app])
    scheduler.add_job(scheduled_weekly_report,  "cron", day_of_week="mon",     hour=9, minute=5,  args=[app])
    scheduler.start()

    logger.info("Bot started with reply keyboard.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
