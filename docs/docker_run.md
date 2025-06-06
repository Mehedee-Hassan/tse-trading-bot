

```
docker run -d \
  --name tse-bot \
  -v /home/run-bot/configs/stock-list/:/app/resource/list/:ro \
  -v /home/run-bot/configs/env/:/app/.env:ro \
  -v /home/run-bot/temp-data/:/app/resource/data/ \
  tse-bot:latest
```