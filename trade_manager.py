import sqlite3
from config import DB_PATH


# ======================================
# CORE LOGIC
# ======================================

def update_positions():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, ticker, entry, stop_loss, take_profit
        FROM signals
        WHERE status = 'OPEN'
    """)

    open_trades = cursor.fetchall()

    if not open_trades:
        print("No open positions.")
        conn.close()
        return

    for trade in open_trades:

        entry_date, ticker, entry, initial_stop, tp = trade

        current_stop = initial_stop
        risk = entry - initial_stop

        if risk <= 0:
            continue

        # ======================================
        # FLOATING PNL (OPEN)
        # ======================================

        cursor.execute("""
            SELECT close
            FROM prices
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT 1
        """, (ticker,))

        latest = cursor.fetchone()

        if latest:
            current_close = latest[0]
            pnl_percent = ((current_close - entry) / entry) * 100

            cursor.execute("""
                UPDATE signals
                SET pnl_percent = ?
                WHERE ticker = ?
                AND status = 'OPEN'
            """, (pnl_percent, ticker))

        # ======================================
        # LOAD CANDLES AFTER ENTRY
        # ======================================

        cursor.execute("""
            SELECT p.date, p.high, p.low, i.ATR14
            FROM prices p
            LEFT JOIN indicators i
            ON p.ticker = i.ticker AND p.date = i.date
            WHERE p.ticker = ?
            AND p.date > ?
            ORDER BY p.date ASC
        """, (ticker, entry_date))

        rows = cursor.fetchall()

        if not rows:
            continue

        for row in rows:

            current_date, high, low, atr = row

            if high is None or low is None:
                continue

            # ======================================
            # 1️⃣ BREAK EVEN (>= 1R)
            # ======================================

            if high >= entry + risk:
                current_stop = max(current_stop, entry)

            # ======================================
            # 2️⃣ TRAILING (>= 1.5R)
            # ======================================

            if atr is not None:
                if high >= entry + 1.5 * risk:
                    trailing_stop = high - atr
                    current_stop = max(current_stop, trailing_stop)

            # ======================================
            # 3️⃣ TP PRIORITY
            # ======================================

            status = None
            exit_price = None

            if high >= tp:
                status = "CLOSED_TP"
                exit_price = tp

            elif low <= current_stop:
                status = "CLOSED_SL"
                exit_price = current_stop

            # ======================================
            # CLOSE POSITION
            # ======================================

            if status:

                result_r = (exit_price - entry) / risk
                percent_result = ((exit_price - entry) / entry) * 100

                cursor.execute("""
                    UPDATE signals
                    SET status = ?,
                        stop_loss = ?,
                        exit_price = ?,
                        exit_date = ?,
                        result_r = ?,
                        percent_result = ?,
                        pnl_percent = NULL
                    WHERE ticker = ?
                    AND status = 'OPEN'
                """, (
                    status,
                    current_stop,
                    exit_price,
                    current_date,
                    result_r,
                    percent_result,
                    ticker
                ))

                message = (
                    f"📊 TRADE CLOSED\n"
                    f"====================\n"
                    f"🎯 Ticker : {ticker}\n"
                    f"📅 Entry  : {entry:.2f}\n"
                    f"💰 Exit   : {exit_price:.2f}\n"
                    f"📌 Status : {status}\n"
                    f"📈 Result : {percent_result:.2f}%\n"
                )


                print(f"{ticker} closed with {status}")

                break

    conn.commit()
    conn.close()
    print("Trade update completed.")


# ======================================
# RUN WRAPPER
# ======================================

def run():
    print("Checking open positions...")
    update_positions()


if __name__ == "__main__":
    run()
