import sqlite3
import requests
import pandas as pd
from datetime import datetime
from config import DB_PATH

# ==============================
# CONFIG
# ==============================

def load_tickers():
    with open("tickers.txt", "r") as f:
        return [line.strip() + ".JK" for line in f.readlines()]
BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"

# ==============================
# INIT DB
# ==============================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            date TEXT,
            ticker TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (date, ticker)
        )
    """)

    conn.commit()
    conn.close()

# ==============================
# FETCH FROM YAHOO
# ==============================

def fetch_ticker(ticker):
    url = f"{BASE_URL}{ticker}?range=6mo&interval=1d"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"HTTP Error {response.status_code} for {ticker}")
            return []

        data = response.json()

        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        indicators = result["indicators"]["quote"][0]

        rows = []

        for i in range(len(timestamps)):
            if indicators["close"][i] is None:
                continue

            date = datetime.fromtimestamp(
                timestamps[i]
            ).strftime("%Y-%m-%d")

            row = {
                "date": date,
                "ticker": ticker.replace(".JK", ""),
                "open": indicators["open"][i],
                "high": indicators["high"][i],
                "low": indicators["low"][i],
                "close": indicators["close"][i],
                "volume": indicators["volume"][i],
            }

            rows.append(row)

        return rows

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return []
# ==============================
# SAVE TO DB
# ==============================

def save_rows(rows):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for row in rows:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO prices
                (date, ticker, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row["date"],
                row["ticker"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"]
            ))
        except Exception as e:
            print("Insert error:", e)

    conn.commit()
    conn.close()

def run():
    print("Initializing database...")
    init_db()

    tickers = load_tickers()

    for ticker in tickers:
        print(f"Fetching {ticker}...")
        rows = fetch_ticker(ticker)

        if rows:
            save_rows(rows)

    print("Fetch completed.")

# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    print("Initializing database...")
    init_db()

    tickers = load_tickers()

    for ticker in tickers:
        print(f"Fetching {ticker}...")
        rows = fetch_ticker(ticker)
        save_rows(rows)

    print("Done.")
