# data_collector.py
from __future__ import annotations
from typing import List, Dict, Set, Tuple
import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import ta
from pathlib import Path
import util
import csv




TZ = ZoneInfo("Asia/Tokyo")
TODAY: str = datetime.now(TZ).date().isoformat() 

ALERTS_FILE: Path = util._load_data_path(TODAY) 
DEFAULT_TICKERS: List[str] = util._load_tickers()

# Row schema: alert_date,ticker,alert_type
_alert_cache: Set[Tuple[str, str, str, int]] | None = None


def _load_alert_cache() -> None:
    global _alert_cache
    if _alert_cache is not None:
        return  

    _alert_cache = set()
    if ALERTS_FILE.exists():
        with ALERTS_FILE.open("r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 4:
                    _alert_cache.add(tuple(row))


def _already_alerted(ticker: str, alert_type: str, value :str) -> bool:
    _load_alert_cache()
    assert _alert_cache is not None
    return (TODAY, ticker, alert_type, value) in _alert_cache


def _mark_alert(ticker: str, alert_type: str, value :str) -> None:
    _load_alert_cache()
    assert _alert_cache is not None
    key = (TODAY, ticker, alert_type, value)
    
    print(key,_alert_cache)
    if key in _alert_cache:
        print("Found previous check flag: ",key)
        return  

    # Append to file first (so even if script crashes later we don’t lose the entry)
    with ALERTS_FILE.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(key)

    _alert_cache.add(key)



def _indicators(df: pd.DataFrame, close_col: str, 
                mega_cap:int=50_000_000_000,
                mid_cap:int=5_000_000_000) -> pd.DataFrame:
    """
    Attach RSI, EMA‑20/50, MACD & signal columns; return NaN‑free frame.
    """
    close = df[close_col]
    df["RSI"] = ta.momentum.RSIIndicator(close).rsi()
    df["EMA20"] = ta.trend.EMAIndicator(close, window=20).ema_indicator()
    df["EMA50"] = ta.trend.EMAIndicator(close, window=50).ema_indicator()
    macd = ta.trend.MACD(close)
    df["MACD"] = macd.macd()
    df["Signal"] = macd.macd_signal()

    df["VALUE_JPY"]   = df["Volume"] * df["Close"]          
    avg_yen_turnover  = df["VALUE_JPY"].rolling(20).mean().iloc[-1]

    # ---- Pick a VOL_REL cutoff by liquidity bucket ----
    if   avg_yen_turnover > mega_cap:        # > ¥50 bn / day  ➜ mega-cap
        vol_cutoff = 1.3                          # 30 % above norm
    elif avg_yen_turnover >  mid_cap:        # ¥5–50 bn / day ➜ mid-cap
        vol_cutoff = 1.6                          # 60 % above norm
    else:                                          # < ¥5 bn / day   ➜ small-cap
        vol_cutoff = 2.0                          # 100 % above norm

    df["VOLUME_ALERT"] = df["VOL_REL"] >= vol_cutoff


    df["BUY_CONFLUENCE"] = (
        (df["MACD"] > df["Signal"])
        & (df["RSI"] > 30)
        & (df["RSI"].rolling(2).min() < 28)
        & (df[close_col] > df["EMA20"])
        & (df["EMA20"] > df["EMA50"])       
    )



    return df.dropna()




def fetch_and_analyze_tse_stocks(
    THREASHOLD_DORP_PERCENTAGE:int = 5,
    THREASHOLD_RSI:int = 30,
    tickers: List[str] | None = None,
    period: str = "3mo",
    interval: str = "1d",
    DEBUG = False
) -> List[Dict]:
    """
    Returns a list of dicts with the latest signal for each qualifying ticker.
    """
    tickers = tickers or DEFAULT_TICKERS
    results: List[Dict] = []

    for ticker in tickers:
        raw = yf.download(ticker, period=period, interval=interval, group_by="ticker")

        if raw.empty:
        
            continue
        if DEBUG:
            print(raw)
            print(raw.columns)
        
        # Flatten MultiIndex → <ticker>_Close
        raw.columns = [f"{c[0]}_{c[1]}" for c in raw.columns]

        if DEBUG:
            print(raw.columns)
        
        close_col = f"{ticker}_Close"

        if DEBUG:
            print("close_col: ", close_col)
    
        if close_col not in raw.columns:
            
            continue
    
        if DEBUG:
            print(raw)


        df = _indicators(raw, close_col)
            
        print("inside 1")

        if df.empty:
            continue

        support = df[close_col].tail(20).min()
        resistance = df[close_col].tail(20).max()
        latest = df.iloc[-1]

        sudden_drop = ((df.iloc[-1][close_col] - df.iloc[-2][close_col]) / df.iloc[-2][close_col]) * 100
        
        if DEBUG:
            print(df.iloc[-1][close_col])
            print(df.iloc[-2][close_col])
            print(sudden_drop)

        if DEBUG:
            print(latest["RSI"])

        name = ""
        try:
            tic = yf.Ticker(ticker)
            info = tic.get_info()              
            name = info.get("longName") \
                or info.get("shortName") \
                or info.get("displayName")
        except Exception as ex:
            print(ex)


        print(f"{ticker} — BUY_CONFLUENCE count in window: {df['BUY_CONFLUENCE'].sum()}")
         

        if latest["BUY_CONFLUENCE"] and not _already_alerted(ticker=ticker, alert_type="BUY", value=str(-1)):
            results.append(
                {
                    "Ticker": ticker,
                    "BUY_SIGNAL":"BUY",
                    "Price": round(latest[close_col], 2),
                    "BuySignal": "Confluence",
                    "RSI": round(latest["RSI"], 2),
                    "MACD Signal": "Buy", 
                    "Support": round(support, 2),
                    "Resistance": round(resistance, 2),
                    "Name": name,
                }
            )
            _mark_alert(ticker=ticker, alert_type="BUY", value=-1)
            continue

        if  latest["RSI"] < THREASHOLD_RSI and not _already_alerted(ticker=ticker, alert_type="RSI", value=str(-1)):
            # and latest[close_col] > latest["EMA20"]:
            results.append(
                {
                    "Ticker": ticker,
                    "Price": round(latest[close_col], 2),
                    "RSI": round(latest["RSI"], 2),
                    "MACD Signal": "Buy"
                    if latest["MACD"] > latest["Signal"]
                    else "Sell",
                    "Support": round(support, 2),
                    "Resistance": round(resistance, 2),
                    "Name" : name
                }
            )
            _mark_alert(ticker=ticker, alert_type="RSI", value=-1)

        if sudden_drop < (-THREASHOLD_DORP_PERCENTAGE) and \
              not _already_alerted(ticker=ticker, alert_type="SuddenDrop", value=str(int(sudden_drop))):
            
            if "Ticker" not in results:
                results.append(
                    {
                        "Ticker": ticker,
                        "SuddenDrop": round(sudden_drop,2),
                        "Price": round(latest[close_col], 2),
                        "RSI": round(latest["RSI"], 2),
                        "MACD Signal": "Buy"
                        if latest["MACD"] > latest["Signal"]
                        else "Sell",
                        "Support": round(support, 2),
                        "Resistance": round(resistance, 2),
                        "Name" : name
                    })
            else:
                results.append(
                    {
                        "SuddenDrop": round(sudden_drop,2)
                    })

            _mark_alert(ticker=ticker, alert_type="SuddenDrop", value=int(sudden_drop))                       
        
        if DEBUG:
            print("result",results)

    return results
