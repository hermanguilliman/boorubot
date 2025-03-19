import asyncio
from datetime import datetime
from typing import List

from aiohttp import ClientSession
from loguru import logger

from app.models.danbooru import DanbooruPost


class DanbooruAPI:
    def __init__(self):
        self.base_url = "https://danbooru.donmai.us"
        self.headers = {"Content-Type": "application/json"}
        self.semaphore = asyncio.Semaphore(5)

    async def get_post(self, post_id: int) -> DanbooruPost:
        """Получает пост по его ID."""
        url = f"{self.base_url}/posts/{post_id}.json"
        async with ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                data = await response.json()
                return DanbooruPost(**data)

    async def get_popular_posts(
        self, page: int = 1, limit: int = 10
    ) -> List[DanbooruPost]:
        """Получает популярные посты за текущий день."""
        url = f"{self.base_url}/explore/posts/popular.json"
        today = datetime.now().strftime("%Y-%m-%d")
        params = {"date": today, "scale": "day", "page": page, "limit": limit}
        async with ClientSession() as session:
            async with session.get(
                url, headers=self.headers, params=params
            ) as response:
                if response.status != 200:
                    logger.debug(
                        f"Ошибка получения популярных постов, статус: {response.status}"
                    )
                    return []
                try:
                    data = await response.json()
                except Exception as e:
                    logger.error(f"Ошибка парсинга JSON: {e}")
                    return []
                if not isinstance(data, list):
                    logger.debug(f"Неожиданный формат данных: {data}")
                    return []
                return [
                    DanbooruPost(**post)
                    for post in data
                    if isinstance(post, dict)
                ]

    async def search_posts(
        self, tags: str, limit: int = 10
    ) -> List[DanbooruPost]:
        """Ищет посты по тегам с заданным лимитом."""
        url = f"{self.base_url}/posts.json"
        params = {"tags": tags, "limit": limit}
        async with self.semaphore:
            await asyncio.sleep(0.5)
            async with ClientSession() as session:
                async with session.get(
                    url, headers=self.headers, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json(
                            content_type="application/json"
                        )
                        return [DanbooruPost(**post) for post in data]
                    else:
                        logger.debug(
                            f"Ошибка поиска постов, статус: {response.status}"
                        )
                        return []
