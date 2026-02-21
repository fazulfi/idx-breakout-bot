import sqlite3
import pandas as pd
from config import DB_PATH


# ==============================
# LOAD INDICATORS (LATEST DATE)
# ==============================
def load_indicators():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql("""
        SELECT *
        FROM indicators
        WHERE date = (SELECT MAX(date) FROM indicators)
        ORDER BY ticker
    """, conn)

    conn.close()
    return df


# ==============================
# SIGNAL LOGIC (TIER 2 ONLY)
# ==============================
def generate_signals(df):

    signals = []

    for _, row in df.iterrows():

        ticker = row["ticker"]
        close = row["close"]
        hh20 = row["HH20"]
        rvol = row["RVOL"]
        atr = row["ATR14"]
        volume = row["volume"]
        value = close * volume

        # ===== OPEN POSITION CHECK =====
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM signals
            WHERE ticker = ? AND status = 'OPEN'
        """, (ticker,))

        open_count = cursor.fetchone()[0]
        conn.close()

        if open_count > 0:
            continue

        if pd.isna(hh20) or pd.isna(rvol) or pd.isna(atr):
            continue

        atr_pct = atr / close

        # ===== TIER 2 BREAKOUT FILTER =====
        if (
            rvol >= 2
            and close >= hh20 * 0.99
            and atr_pct >= 0.01
        ):

            entry = close
            stop = close - atr
            tp = close + (2 * atr)

            signals.append({
                "date": row["date"],
                "ticker": ticker,
                "signal_type": "BREAKOUT_T2",
                "entry": entry,
                "stop_loss": stop,
                "take_profit": tp,
                "rvol": rvol,
                "atr": atr,
                "volume": volume,
                "value": value,
                "status": "OPEN",
    })

    return pd.DataFrame(signals)


# ==============================
# SAVE TO DB
# ==============================
def save_signals(df):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO signals
            (date, ticker, signal_type, entry, stop_loss, take_profit, rvol, atr, volume, value, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["date"],
            row["ticker"],
            row["signal_type"],
            row["entry"],
            row["stop_loss"],
            row["take_profit"],
            row["rvol"],
            row["atr"],
            row["volume"],
            row["value"],
            row["status"],
        ))

    conn.commit()
    conn.close()


# ====================================
# RUN WRAPPER
# ====================================

def run():
    print("Loading indicators...")
    df = load_indicators()

    if df.empty:
        print("No indicator data found.")
        return

    print("Generating signals...")
    signal_df = generate_signals(df)

    if signal_df.empty:
        print("No new signals.")
        return

    print("Saving signals...")
    save_signals(signal_df)

    print("Signal generation completed.")

if __name__ == "__main__":
    run()
