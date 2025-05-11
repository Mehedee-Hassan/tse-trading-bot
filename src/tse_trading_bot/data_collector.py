# data_collector.py
from __future__ import annotations
from typing import List, Dict
import yfinance as yf
import pandas as pd
import ta
from pathlib import Path
import util




DEFAULT_TICKERS: List[str] = util._load_tickers()


def _indicators(df: pd.DataFrame, close_col: str) -> pd.DataFrame:
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
        print(close_col)
        if close_col not in raw.columns:
            
            continue
    
        if DEBUG:
            print(raw)


        df = _indicators(raw, close_col)
            


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


        if  latest["RSI"] < THREASHOLD_RSI :
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
        if sudden_drop < (-THREASHOLD_DORP_PERCENTAGE):
            
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
        
        if DEBUG:
            print("result",results)

    return results
