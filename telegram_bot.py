import sqlite3
import requests
from config import DB_PATH, TELEGRAM_TOKEN, CHAT_ID


# ===============================
# LOAD SIGNALS FROM DATABASE
# ===============================
def load_signals():
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT date, ticker, signal_type, entry, stop_loss, take_profit,
           rvol, atr, volume, value
    FROM signals
    WHERE date = (SELECT MAX(date) FROM signals)
    ORDER BY rvol DESC
    """

    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return rows


# ===============================
# FORMAT MESSAGE
# ===============================
def format_message(signals):
    if not signals:
        return "📭 Tidak ada sinyal breakout hari ini."

    message = "🚀 *IDX Breakout Scanner*\n"
    message += "==========================\n\n"

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
            value
        ) = row

        # Safety fallback (hindari None crash)
        entry = entry or 0
        stop = stop or 0
        tp = tp or 0
        rvol = rvol or 0
        atr = atr or 0
        volume = volume or 0
        value = value or 0

        message += f"📈 *{ticker}* ({signal_type})\n"
        message += f"Entry : {entry:,.2f}\n"
        message += f"SL    : {stop:,.2f}\n"
        message += f"TP    : {tp:,.2f}\n"
        message += f"RVOL  : {rvol:.2f}\n"
        message += f"ATR   : {atr:,.2f}\n"
        message += f"Vol   : {volume:,.0f}\n"
        message += f"Value : {value/1_000_000_000:,.2f} B\n"
        message += "--------------------------\n"

    return message

# ===============================
# SEND TO TELEGRAM
# ===============================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": None
    }

    response = requests.post(url, data=payload)
    return response.json()

# ====================================
# RUN WRAPPER
# ====================================

def run():
    print("Loading signals...")
    signals = load_signals()

    print("Formatting message...")
    message = format_message(signals)

    print("Sending to Telegram...")
    result = send_telegram(message)

    print("Telegram send completed.")
    print(result)

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    run()
