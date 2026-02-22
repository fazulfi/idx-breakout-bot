import sqlite3
from config import DB_PATH, TELEGRAM_TOKEN

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
# =========================
# LOAD DATA
# =========================
def load_signals():
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT date, ticker, signal_type, entry, stop_loss, take_profit,
           rvol, atr, volume, value
    FROM signals
    WHERE date = (SELECT MAX(date) FROM signals)
    ORDER BY value DESC
    LIMIT 10
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return rows

# =========================
# LOAD PERFORMANCE
# =========================
def load_performance():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN status = 'CLOSED_TP' THEN 1 ELSE 0 END) as win,
        AVG(CASE WHEN status = 'CLOSED_TP' THEN percent_result END) as avg_gain,
        AVG(CASE WHEN status = 'CLOSED_SL' THEN percent_result END) as avg_loss
    FROM signals
    WHERE status IN ('CLOSED_TP', 'CLOSED_SL')
    """

    cursor.execute(query)
    row = cursor.fetchone()
    conn.close()

    return row
# =========================
# LOAD CLOSED
# =========================
def load_closed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT ticker, signal_type, entry, stop_loss, take_profit,
           percent_result, exit_date
    FROM signals
    WHERE status IN ('CLOSED_TP', 'CLOSED_SL')
    ORDER BY exit_date DESC
    LIMIT 10
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return rows


# =========================
# FORMAT MESSAGE
# =========================
def format_open(signals):
    if not signals:
        return "📭 <b>Tidak ada sinyal breakout hari ini.</b>"

    message = "<b>📂 OPEN SIGNALS</b>\n"
    message += "━━━━━━━━━━━━━━━━━━\n\n"

    for row in signals:
        (
            date,
            ticker,
            signal_type,
            entry,
            stop,
            tp,
            rvol,
            atr,
            volume,
            value,
        ) = row

        entry = entry or 0
        stop = stop or 0
        tp = tp or 0

        message += f"<b>{ticker}</b> ({signal_type})\n"
        message += f"Entry : {entry:,.2f}\n"
        message += f"SL    : {stop:,.2f}\n"
        message += f"TP    : {tp:,.2f}\n"
        message += "━━━━━━━━━━━━━━━━━━\n"

    return message
# =========================
# FORMAT CLOSED
# =========================
def format_closed(rows):
    if not rows:
        return "📭 <b>No closed trades yet.</b>"

    message = "✅ <b>CLOSED SIGNALS</b>\n"
    message += "──────────────────\n\n"

    for row in rows:
        ticker, signal_type, entry, sl, tp, percent, exit_date = row

        message += f"<b>{ticker}</b> ({signal_type})\n"
        message += f"Entry : {entry:.2f}\n"
        message += f"SL    : {sl:.2f}\n"
        message += f"TP    : {tp:.2f}\n"
        message += f"Result: {percent:.2f}%\n"
        message += f"Exit  : {exit_date}\n"
        message += "──────────────────\n"

    return message

# =========================
# PERFORMA MESSAGE
# =========================
def format_performance():
    data = load_performance()

    if not data:
        return "📊 <b>No performance data yet.</b>"

    total, win, avg_gain, avg_loss = data

    win = win or 0
    total = total or 0
    avg_gain = avg_gain or 0
    avg_loss = avg_loss or 0

    winrate = (win / total * 100) if total > 0 else 0

    message = "<b>📊 PERFORMANCE SUMMARY</b>\n"
    message += "━━━━━━━━━━━━━━\n"
    message += f"Total Trades : {total}\n"
    message += f"Winrate      : {winrate:.2f}%\n"
    message += f"Avg Gain     : {avg_gain:.2f}%\n"
    message += f"Avg Loss     : {avg_loss:.2f}%\n"

    return message


# =========================
# MENU
# =========================
def main_menu():
    keyboard = [
        ["📂 Open Signals"],
        ["✅ Closed Signals"],
        ["📊 Performance"],
        ["🚪 Exit"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 IDX Breakout System\n\nSelect menu:",
        reply_markup=main_menu()
    )

# =========================
# BUTTON HANDLER
# =========================
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📂 Open Signals":
        signals = load_signals()
        message = format_open(signals)
        await update.message.reply_text(message, parse_mode="HTML")

    elif text == "✅ Closed Signals":
        rows = load_closed()
        message = format_closed(rows)
        await update.message.reply_text(message, parse_mode="HTML")

    elif text == "📊 Performance":
        message = format_performance()
        await update.message.reply_text(message, parse_mode="HTML")

    elif text == "🚪 Exit":
        from telegram import ReplyKeyboardRemove
        await update.message.reply_text(
            "Menu closed.",
            reply_markup=ReplyKeyboardRemove()
        )
# =========================
# MAIN
# =========================
def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
