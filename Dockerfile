FROM python:3.13-slim

WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN pip install --upgrade pip --root-user-action=ignore && \
    pip install --no-cache-dir poetry --root-user-action=ignore && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi
COPY . /app
CMD ["python", "bot.py"]