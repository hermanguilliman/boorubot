from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.services.danbooru import DanbooruService


class DanbooruMiddleware(BaseMiddleware):
    def __init__(self, danbooru_service: DanbooruService):
        self.service = danbooru_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["danbooru"] = self.service
        return await handler(event, data)
