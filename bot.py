import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import DeleteWebhook
from aiogram_dialog import setup_dialogs
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from app.commands import set_default_commands
from app.config import logger_setup
from app.dialogs.main_dialog import dialog
from app.filters.is_admin import AdminFilter
from app.handlers.start import start
from app.middlewares.danbooru import DanbooruMiddleware
from app.middlewares.repo import RepoMiddleware
from app.middlewares.scheduler import SchedulerMiddleware
from app.models.base import Base
from app.services.danbooru import DanbooruService

load_dotenv()


async def create_schema(engine: AsyncEngine):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.error(e)


async def main():
    bot_token: str | None = os.getenv("BOT")
    admin_id: str | None = os.getenv("ADMIN")

    if not bot_token:
        logger.error("Не найден токен телеграм бота!")
        exit()
    if not admin_id:
        logger.error("Не найден id администратора!")
        exit()

    url = "sqlite+aiosqlite:///database/db.sqlite"
    engine = create_async_engine(url, echo=False, future=True)
    await create_schema(engine)
    sessionmaker = async_sessionmaker(
        engine, expire_on_commit=False, autoflush=False
    )
    storage = MemoryStorage()
    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=storage)
    danbooru = DanbooruService(sessionmaker, bot, admin_id)
    scheduler = AsyncIOScheduler()
    await set_default_commands(bot)

    dp.include_router(dialog)
    setup_dialogs(dp)
    dp.update.middleware(RepoMiddleware(sessionmaker))
    dp.update.middleware(
        DanbooruMiddleware(
            sessionmaker=sessionmaker, bot=bot, admin_id=int(admin_id)
        )
    )
    dp.update.middleware(SchedulerMiddleware(scheduler))
    dp.message.register(start, CommandStart(), AdminFilter(int(admin_id)))

    logger_setup()

    scheduler.add_job(
        danbooru.check_new_posts,
        "interval",
        hours=1,
    )
    scheduler.start()

    logger.debug("Бот запущен")
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
