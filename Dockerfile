FROM python:3.13-alpine

RUN apk update

WORKDIR /boorubot

RUN pip install --upgrade pip --root-user-action=ignore && \
    pip install --no-cache-dir poetry

COPY poetry.lock pyproject.toml /boorubot/

RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-ansi --no-cache --no-interaction

COPY . /boorubot
CMD ["python", "bot.py"]