FROM ghcr.io/astral-sh/uv:python3.14-alpine

WORKDIR /boorubot

COPY uv.lock pyproject.toml /boorubot/

RUN uv pip install --system --no-cache-dir -r <(uv export --no-hashes)

COPY . /boorubot/

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]