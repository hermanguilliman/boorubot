import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, ExceptionTypeFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import DeleteWebhook
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from environs import load_dotenv
from loguru import logger
from pybooru import Danbooru
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.commands import set_default_commands
from app.config import logger_setup
from app.dialogs.main_dialog import dialog
from app.filters.is_admin import AdminFilter
from app.handlers.start import start
from app.handlers.unknown_errors import on_unknown_intent, on_unknown_state
from app.middlewares.repo import RepoMiddleware
from app.middlewares.scheduler import SchedulerMiddleware
from app.services.danbooru import check_new_posts

load_dotenv()


async def create_schema(async_sessionmaker: async_sessionmaker[AsyncSession]):
    async with async_sessionmaker() as session:
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
    storage = MemoryStorage()
    bot = Bot(token=bot_token, parse_mode="HTML")
    dp = Dispatcher(storage=storage)
    danbooru = Danbooru("danbooru")
    scheduler = AsyncIOScheduler()
    await create_schema(sessionmaker)
    await set_default_commands(bot)

    dp.errors.register(
        on_unknown_intent,
        ExceptionTypeFilter(UnknownIntent),
    )
    dp.errors.register(
        on_unknown_state,
        ExceptionTypeFilter(UnknownState),
    )

    dp.include_router(dialog)
    setup_dialogs(dp)
    dp.update.middleware(RepoMiddleware(sessionmaker))
    dp.update.middleware(SchedulerMiddleware(scheduler))
    dp.message.register(start, CommandStart(), AdminFilter(admin_id))

    logger_setup()

    scheduler.add_job(
        check_new_posts,
        "interval",
        hours=1,
        args=(bot, sessionmaker, danbooru, admin_id),
    )
    scheduler.start()

    logger.debug("Бот запущен")
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
