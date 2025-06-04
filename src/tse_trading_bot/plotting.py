import matplotlib.pyplot as plt
import pandas as pd

def plot_indicators(df: pd.DataFrame, ticker: str, close_col: str, show_last_n: int = 60):
    df = df.tail(show_last_n)

    fig, axs = plt.subplots(3, 1, figsize=(14, 10), sharex=True, gridspec_kw={"height_ratios": [3, 2, 2]})
    
    # Price + EMA
    axs[0].plot(df.index, df[close_col], label="Close", linewidth=2)
    axs[0].plot(df.index, df["EMA20"], label="EMA20", linestyle='--')
    axs[0].plot(df.index, df["EMA50"], label="EMA50", linestyle='--')
    
    buy_signals = df[df["BUY_CONFLUENCE"]]
    axs[0].scatter(buy_signals.index, buy_signals[close_col], color="green", label="Buy Signal", marker="^", s=100)
    
    axs[0].set_title(f"{ticker} Price + EMAs + Buy Signal")
    axs[0].legend()
    axs[0].grid(True)

    # MACD
    axs[1].plot(df.index, df["MACD"], label="MACD", color="blue")
    axs[1].plot(df.index, df["Signal"], label="Signal", color="orange")
    axs[1].bar(df.index, df["MACD"] - df["Signal"], label="MACD Histogram", color="gray", alpha=0.4)
    axs[1].legend()
    axs[1].grid(True)
    axs[1].set_title("MACD")

    # RSI
    axs[2].plot(df.index, df["RSI"], label="RSI", color="purple")
    axs[2].axhline(30, linestyle='--', color="red", alpha=0.5)
    axs[2].axhline(70, linestyle='--', color="green", alpha=0.5)
    axs[2].legend()
    axs[2].grid(True)
    axs[2].set_title("RSI")

    plt.tight_layout()
    plt.show()
