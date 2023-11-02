import asyncio
import os
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.filters.command import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from environs import load_dotenv
from loguru import logger

from app.commands import set_default_commands
from app.config import logger_setup
from app.filters.is_admin import AdminFilter
from app.handlers.add import add_sub
from app.handlers.delete import delete_sub
from app.handlers.start import start
from app.handlers.subs import show_subs
from app.middlewares.db import DatabaseMiddleware
from app.services.danbooru import check_new_posts

load_dotenv()


async def create_schema(conn: sqlite3.Connection):
    with open("database/init.sql") as f:
        script = f.read()
        conn.executescript(script)


async def main():
    bot_token: str = os.getenv("BOT")
    admin_id: int = int(os.getenv("ADMIN"))

    if not bot_token:
        logger.error("Не найден токен телеграм бота!")
        exit()
    if not admin_id:
        logger.error("Не найден id администратора!")
        exit()

    bot = Bot(token=bot_token, parse_mode="HTML")
    dp = Dispatcher()
    scheduler = AsyncIOScheduler()
    conn = sqlite3.connect("database/db.sqlite")
    await create_schema(conn)
    await set_default_commands(bot)
    dp.message.register(start, Command("start"), AdminFilter(admin_id))
    dp.message.register(add_sub, Command("add"), AdminFilter(admin_id))
    dp.message.register(delete_sub, Command("del"), AdminFilter(admin_id))
    dp.message.register(show_subs, Command("subs"), AdminFilter(admin_id))
    dp.message.middleware(DatabaseMiddleware(conn))

    logger_setup()

    scheduler.add_job(check_new_posts, "interval", hours=1, args=(bot, conn, admin_id))
    scheduler.start()

    logger.debug("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
