FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /boorubot

COPY pyproject.toml /boorubot/

RUN uv pip install --system --no-cache-dir -r <(uv export --no-hashes)

COPY . /boorubot

CMD ["python", "bot.py"]