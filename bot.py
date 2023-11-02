import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters.command import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from environs import load_dotenv
from loguru import logger
from pybooru import Danbooru
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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


async def create_schema(async_sessionmaker: async_sessionmaker[AsyncSession]):
    async with async_sessionmaker() as session:
        async with session.begin():
            try:
                with open("database/init.sql") as file:
                    lines = file.readlines()
                    for line in lines:
                        await session.execute(text(line))
            except Exception as e:
                logger.error(e)


async def main():
    bot_token: str = os.getenv("BOT")
    admin_id: int = int(os.getenv("ADMIN"))

    if not bot_token:
        logger.error("Не найден токен телеграм бота!")
        exit()
    if not admin_id:
        logger.error("Не найден id администратора!")
        exit()

    url = "sqlite+aiosqlite:///database/db.sqlite"
    engine = create_async_engine(url, echo=False, future=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    bot = Bot(token=bot_token, parse_mode="HTML")
    dp = Dispatcher()
    danbooru = Danbooru("danbooru")
    scheduler = AsyncIOScheduler()
    await create_schema(sessionmaker)
    await set_default_commands(bot)
    dp.message.register(start, Command("start"), AdminFilter(admin_id))
    dp.message.register(add_sub, Command("add"), AdminFilter(admin_id))
    dp.message.register(delete_sub, Command("del"), AdminFilter(admin_id))
    dp.message.register(show_subs, Command("subs"), AdminFilter(admin_id))
    dp.message.middleware(DatabaseMiddleware(sessionmaker))

    logger_setup()

    scheduler.add_job(
        check_new_posts,
        "interval",
        minutes=1,
        args=(bot, sessionmaker, danbooru, admin_id),
    )
    scheduler.start()

    logger.debug("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
