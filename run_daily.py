# ==========================================
# RUN DAILY PIPELINE (GLOBAL ORCHESTRATOR)
# ==========================================

from datetime import datetime
import traceback

# Import RUN wrappers
from fetch_data import run as run_fetch
from trade_manager import run as run_trade
from calculate import run as run_calculate
from signal_engine import run as run_signal


def main():

    print("=" * 60)
    print("🚀 STARTING DAILY PIPELINE")
    print("Time :", datetime.now())
    print("=" * 60)

    try:

        # =========================
        # 1️⃣ FETCH DATA
        # =========================
        print("\n[1/5] Fetching latest market data...")
        run_fetch()
        print("✓ Fetch completed")

        # =========================
        # 2️⃣ UPDATE OPEN POSITIONS
        # =========================
        print("\n[2/5] Updating open positions (TP/SL)...")
        run_trade()
        print("✓ Position update completed")

        # =========================
        # 3️⃣ CALCULATE INDICATORS
        # =========================
        print("\n[3/5] Calculating indicators...")
        run_calculate()
        print("✓ Indicator calculation completed")

        # =========================
        # 4️⃣ GENERATE SIGNALS
        # =========================
        print("\n[4/5] Generating new signals...")
        run_signal()
        print("✓ Signal generation completed")

        print("\n🎉 DAILY PIPELINE FINISHED SUCCESSFULLY")

    except Exception as e:
        print("\n❌ ERROR OCCURRED:")
        print(str(e))
        traceback.print_exc()


if __name__ == "__main__":
    main()
