from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from app.services.repo import Repo
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        self._async_sessionmaker = sessionmaker
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        async with self._async_sessionmaker() as session:
            async with session.begin():
                data["repo"] = Repo(session)
                return await handler(event, data)