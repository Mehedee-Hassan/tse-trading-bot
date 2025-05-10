# bot_manual.py
"""
One‑shot Tokyo‑Stock scan & push.

Usage:
    $ python bot_manual.py
"""

from __future__ import annotations
import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

import data_collector                  # your existing module

# ───────── Config ──────────
load_dotenv()                          # reads .env
TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")        # group ID or user ID (str)

# ───────── Helpers ─────────
def _format(results: list[dict]) -> str:

    heading = f"📈 Tokyo Stock Scan ({datetime.now(ZoneInfo('Asia/Tokyo')).date()})\n\n"
    
    if not results:
        return heading + "No qualifying TSE stocks today."
    

    results_with_drop = [r for r in results if "SuddenDrop" in r]
    results_with_no_drop = [r for r in results if "SuddenDrop" not in r]
    

    message  = ''
    message_with_drop = ''
    if len(results_with_no_drop) > 0:
        message =  heading + "\n".join(
            f"{r['Ticker']}  |  ¥{r['Price']}\n"
            f"RSI {r['RSI']} • MACD {r['MACD Signal']}\n"
            f"Support ¥{r['Support']} / Resistance ¥{r['Resistance']}\n"
            for r in results_with_no_drop
        )
    if len(results_with_drop) > 0:

        message_with_drop =  f"\n**PRICE DROP ALERT !!! {datetime.now(ZoneInfo('Asia/Tokyo')).date()}"  + "\n".join(
            f"\n{r['Ticker']}  | ¥{r['Price']}\n"
            f"\n{ abs(r['SuddenDrop']) } % Drop !!\n"
            f"RSI {r['RSI']} • MACD {r['MACD Signal']}\n"
            f"Support ¥{r['Support']} / Resistance ¥{r['Resistance']}\n"
            for r in results_with_drop
        )

    additionals = f"\n Trading View: https://www.tradingview.com/chart/ \n" \
                   "Rakuten Security: https://www.rakuten-sec.co.jp\n"

    return message + message_with_drop + additionals


def _send_telegram(text: str) -> None:
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing")

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": text},
        timeout=30,
    )

    # ─── Debug helper ───
    if not resp.ok:                       # resp.ok is False for 4xx/5xx
        print(f"Telegram error {resp.status_code}: {resp.text}")  
    resp.raise_for_status()

    print("✅  Message sent")



# ───────── Main ──────────
if __name__ == "__main__":
    message = _format(data_collector.fetch_and_analyze_tse_stocks())
    _send_telegram(message)
