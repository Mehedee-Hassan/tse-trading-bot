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
import util

import data_collector                 

# ───────── Config ──────────
load_dotenv()                         
TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")     
THREASHOLD_DORP_PERCENTAGE = os.getenv("THREASHOLD_DORP_PERCENTAGE",5)
THREASHOLD_RSI = os.getenv("THREASHOLD_RSI") 
MESSAGE_BATCH_SIZE = os.getenv("MESSAGE_BATCH_SIZE",15) 
BATCH_MODE = os.getenv("BATCH_MODE","TRUE")
THREASHOLD_AVG_DORP_PERCENTAGE = os.getenv("THREASHOLD_AVG_DORP_PERCENTAGE",5)

# ───────── Helpers ─────────
def _format(results: list[dict],additionals_flag: bool=False) -> str:

    heading = f"📈 Tokyo Stock Scan ({datetime.now(ZoneInfo('Asia/Tokyo')).date()})\n\n"
    
    if not results:
        return {"flag":"empty", "message":heading + "No qualifying TSE stocks today."}
    

    results_with_drop = []
    results_with_no_drop = []
    resutls_with_buy =[]
    results_with_drop_avg = []
    
    for r in results:

        if "BUY_SIGNAL" in r:
            resutls_with_buy.append(r)
        
        elif "SuddenDrop" in r:
            results_with_drop.append(r)
        elif "AVG_DROP" in r:
            results_with_drop_avg.append(r)
        else:
            results_with_no_drop.append(r)


    message  = ''
    message_with_drop = ''
    message_with_buy = ''
    message_with_avg_drop = ''
    if len(results_with_no_drop) > 0:
        message =  f"\n⬇️ RSI Signal ({datetime.now(ZoneInfo('Asia/Tokyo')).date()})\n\n" + "\n".join(
            f"{r['Ticker']}  | {r['Name']} |  ¥{r['Price']}\n"
            f"RSI {r['RSI']} • "
            f"Support ¥{r['Support']} / Resistance ¥{r['Resistance']}\n"
            f"Market CAP:{ r['CAP']} \n" if r['CAP'] is not None else ""
            for r in results_with_no_drop
        )
    if len(results_with_drop) > 0:

        message_with_drop =  f"\n🚨SUDDEN PRICE DROP ALERT !!! {datetime.now(ZoneInfo('Asia/Tokyo')).date()}"  + "\n".join(
            f"\n{r['Ticker']} | {r['Name']} | ¥{r['Price']}\n"
            f"\n{ abs(r['SuddenDrop']) } % Drop !!\n"
            f"RSI {r['RSI']} • MACD {r['MACD Signal']}\n"
            f"Support ¥{r['Support']} / Resistance ¥{r['Resistance']}\n"
            f"Market CAP:{ r['CAP']} \n" if r['CAP'] is not None else ""
            for r in results_with_drop
        )

    if len(results_with_drop_avg) > 0:

        message_with_avg_drop =  f"\n📉AVG PRICE DROP ALERT !!! {datetime.now(ZoneInfo('Asia/Tokyo')).date()}"  + "\n".join(
            f"\n{r['Ticker']} | {r['Name']} | ¥{r['Price']}\n"
            f"\n{ abs(r['AVG_DROP']) } % Drop !!\n"
            f"RSI {r['RSI']} • MACD {r['MACD Signal']}\n"
            f"Support ¥{r['Support']} / Resistance ¥{r['Resistance']}\n"
            f"Market CAP:{ r['CAP']} \n" if r['CAP'] is not None else ""
            for r in results_with_drop_avg
        )

    if len(resutls_with_buy) > 0:

        message_with_buy =  f"\n\n🔥🚦 BUY SIGNAL!!! {datetime.now(ZoneInfo('Asia/Tokyo')).date()}"  + "\n".join(
            f"\n{r['Ticker']} | {r['Name']} | ¥{r['Price']}\n"
            f"Market CAP:{ r['CAP']} \n" if r['CAP'] is not None else ""
            f"RSI {r['RSI']} • MACD {r['MACD Signal']}\n"
            f"Support ¥{r['Support']} / Resistance ¥{r['Resistance']}\n"
            for r in resutls_with_buy
        )

    additionals = ''
    if additionals_flag:
        additionals = f"\nTrading View: https://www.tradingview.com/chart/ \n" \
                    "Rakuten Security: https://www.rakuten-sec.co.jp\n"

    return {
        "flag":"message", 
        "message": message_with_buy 
        + message 
        + message_with_drop 
        + message_with_avg_drop
        + additionals
        }


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





def send_message(tickers:list[str] | None = None):
    """
    Fetch, analyse and (optionally) push a Telegram message.

    Returns
    -------
    bool
        True  – a message WAS sent
        False – the result set was empty, nothing was sent
    """

    message = _format(data_collector.fetch_and_analyze_tse_stocks(
                THREASHOLD_DORP_PERCENTAGE=int(THREASHOLD_DORP_PERCENTAGE),
                THREASHOLD_AVG_DORP_PERCENTAGE=int(THREASHOLD_AVG_DORP_PERCENTAGE),
                THREASHOLD_RSI = int(THREASHOLD_RSI),
                tickers=tickers
            ))
    if message["flag"] == "empty":
        return False
    
    print(message["message"])
            
    # _send_telegram(message["message"])

    return True


    

def batch_load_message(message_batch_size=20):
    full_stock_list = util._load_tickers()

    increment = 0
    message_sent = False
    message_sent_once = False

    while increment + message_batch_size < len(full_stock_list):

        batch_list = full_stock_list[increment:increment + message_batch_size]
        message_sent  = send_message(tickers=batch_list)

        increment += message_batch_size

        if not message_sent_once and not message_sent:
            message_sent_once = True


    batch_list = full_stock_list[increment:increment + message_batch_size]
    message_sent = send_message(tickers=batch_list)


    if not message_sent and not message_sent_once:
        _send_telegram(_format(results={})["message"])
    



# ───────── Main ──────────
if __name__ == "__main__":


    if BATCH_MODE == "TRUE":
        batch_load_message(message_batch_size=int(MESSAGE_BATCH_SIZE))
    else:
        
        send_message()