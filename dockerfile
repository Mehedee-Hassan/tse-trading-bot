FROM python:3.11-slim

ENV POETRY_VERSION=1.8.2
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi


COPY . /app

CMD ["python", "./src/tse_trading_bot/bot_manual.py"]
