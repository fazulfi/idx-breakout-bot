import sqlite3
import pandas as pd
from ta.volatility import AverageTrueRange
from config import DB_PATH


# ====================================
# LOAD PRICE DATA
# ====================================

def load_price_data():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql("""
        SELECT *
        FROM prices
        ORDER BY ticker, date
    """, conn)

    conn.close()
    return df


# ====================================
# CALCULATE INDICATORS
# ====================================

def calculate_indicators(df):

    results = []

    tickers = df["ticker"].unique()

    for ticker in tickers:

        stock_df = df[df["ticker"] == ticker].copy()

        if len(stock_df) < 20:
            continue

        stock_df = stock_df.sort_values("date")

        # === HH20 & LL20 ===
        stock_df["HH20"] = stock_df["high"].rolling(20).max()
        stock_df["LL20"] = stock_df["low"].rolling(20).min()

        # === AVG VOL 20 ===
        stock_df["AVG_VOL20"] = stock_df["volume"].rolling(20).mean()

        # === RVOL ===
        stock_df["RVOL"] = stock_df["volume"] / stock_df["AVG_VOL20"]

        # === ATR 14 ===
        atr_indicator = AverageTrueRange(
            high=stock_df["high"],
            low=stock_df["low"],
            close=stock_df["close"],
            window=14
        )

        stock_df["ATR14"] = atr_indicator.average_true_range()

        # === VALUE (Money Flow) ===
        stock_df["value"] = stock_df["close"] * stock_df["volume"]

        latest = stock_df.iloc[-1]

        result = {
            "date": latest["date"],
            "ticker": ticker,
            "close": latest["close"],
            "volume": latest["volume"],
            "value": latest["value"],
            "HH20": latest["HH20"],
            "LL20": latest["LL20"],
            "ATR14": latest["ATR14"],
            "AVG_VOL20": latest["AVG_VOL20"],
            "RVOL": latest["RVOL"],
        }

        results.append(result)

    return pd.DataFrame(results)


# ====================================
# SAVE TO DATABASE
# ====================================

def save_indicators(df):

    if df.empty:
        print("No indicators to save.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            date TEXT,
            ticker TEXT,
            close REAL,
            volume REAL,
            value REAL,
            HH20 REAL,
            LL20 REAL,
            ATR14 REAL,
            AVG_VOL20 REAL,
            RVOL REAL,
            PRIMARY KEY (date, ticker)
        )
    """)

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO indicators
            (date, ticker, close, volume, value, HH20, LL20, ATR14, AVG_VOL20, RVOL)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["date"],
            row["ticker"],
            row["close"],
            row["volume"],
            row["value"],
            row["HH20"],
            row["LL20"],
            row["ATR14"],
            row["AVG_VOL20"],
            row["RVOL"],
        ))

    conn.commit()
    conn.close()


# ====================================
# RUN WRAPPER
# ====================================

def run():
    print("Loading price data...")
    df = load_price_data()

    if df.empty:
        print("No price data found.")
        return

    print("Calculating indicators...")
    result_df = calculate_indicators(df)

    print("Saving indicators...")
    save_indicators(result_df)

    print("Indicators calculation completed.")
