FROM python:3.11-slim

WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi
COPY . /app
CMD ["python", "bot.py"]