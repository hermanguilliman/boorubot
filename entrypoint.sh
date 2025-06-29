#!/bin/sh
alembic upgrade head
exec python bot.py