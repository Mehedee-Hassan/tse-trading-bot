## INTRODUCTION

Trading bot to send stock information to telegram channel


## Commands

```
curl -sSL https://install.python-poetry.org | python3 -

```


```
poetry add yfinance pandas numpy ta matplotlib python-telegram-bot
```

### RUN BOT 

#### Step1: Setup `.env` file.
1. telegram channel id, token, and common env variables.
   
#### Step2: Make List and Run
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

### DOCKER FILE

```
docker build -t tse-trading-bot-v1 .
```
```
docker run tse-trading-bot-v1
```


### Demo
[demo](docs/message_demo.md)
