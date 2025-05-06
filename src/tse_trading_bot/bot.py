
from __future__ import annotations
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo         
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

import data_collector

# ───────── Config ──────────
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ───────── Logging ─────────
logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s: %(message)s", level=logging.INFO
)
log = logging.getLogger(__name__)


def _format(results: list[dict]) -> str:
    heading = f"📈 Tokyo Stock Scan ({datetime.now(ZoneInfo('Asia/Tokyo')).date()})\n\n"
    if not results:
        return heading + "No qualifying TSE stocks today."
    return heading + "\n".join(
        f"{r['Ticker']}  |  ¥{r['Price']}\n"
        f"RSI {r['RSI']} • MACD {r['MACD Signal']}\n"
        f"Support ¥{r['Support']} / Resistance ¥{r['Resistance']}\n"
        for r in results
    )


# ───────── Command handlers ──────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👋 Hi!  Send /scan whenever you want today’s Tokyo scan.",
    )


async def scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    msg = _format(data_collector.fetch_and_analyze_tse_stocks())
    await ctx.bot.send_message(chat_id=update.effective_chat.id, text=msg)


# ───────── Main ──────────
def main() -> None:
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    log.info("Bot up ⬆️")
    app.run_polling(allowed_updates=["message", "edited_message"])


if __name__ == "__main__":
    main()
