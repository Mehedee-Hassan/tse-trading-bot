## INTRODUCTION

Trading bot to send stock information to telegram channel


## Commands

```
curl -sSL https://install.python-poetry.org | python3 -

```
```
pip install -r requirement.txt
```

```
poetry add yfinance pandas numpy ta matplotlib python-telegram-bot
```

### RUN BOT 
1. update `resource/ticker.txt` list of stock.
2. run command.

```
poetry run python src/tse_trading_bot/bot.py
```
in cannel
```
/scan
```

### ONE-TIME SCAN 
```
poetry run python src/tse_trading_bot/bot_manual.py
```


### Demo
[demo](!docs/message_demo.md)
