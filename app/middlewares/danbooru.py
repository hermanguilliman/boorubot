from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.danbooru import DanbooruService


class DanbooruMiddleware(BaseMiddleware):
    def __init__(
        self,
        session_pool: async_sessionmaker[AsyncSession],
        bot: Bot,
        admin_id: int,
    ):
        self.session_pool = session_pool
        self.bot = bot
        self.admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["danbooru"] = DanbooruService(
            session_pool=self.session_pool,
            bot=self.bot,
            admin_id=self.admin_id,
        )
        return await handler(event, data)
