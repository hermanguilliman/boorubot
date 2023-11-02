from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlite3 import Connection
from app.services.repo import Repo


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, connection: Connection):
        self.connection = connection
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        data["connection"] = self.connection
        data["repo"] = Repo(self.connection)
        return await handler(event, data)