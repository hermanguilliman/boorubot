import asyncio
from datetime import datetime
from typing import List

from aiohttp import ClientResponseError, ClientSession
from loguru import logger

from app.models.danbooru import DanbooruPost


class DanbooruAPI:
    def __init__(self):
        self.base_url = "https://danbooru.donmai.us"
        self.headers = {"Content-Type": "application/json"}
        self.rate_limiter = RateLimiter(max_calls=5, period=1)
        self.server_error_backoff = 60  # Задержка в секундах при ошибке сервера

    async def _make_request(self, url: str, params: dict = None) -> dict | None:
        """Вспомогательная функция для выполнения HTTP-запросов с повторными попытками."""
        retries = 3
        for attempt in range(retries):
            await self.rate_limiter.acquire()
            async with ClientSession() as session:
                try:
                    async with session.get(
                        url, headers=self.headers, params=params
                    ) as response:
                        if response.status == 200:
                            return await response.json(content_type="application/json")
                        elif response.status == 429:
                            wait_time = 2**attempt
                            logger.debug(
                                f"Ошибка 429, повторная попытка через {wait_time} секунд"
                            )
                            await asyncio.sleep(wait_time)
                        elif response.status >= 500:
                            logger.error(
                                f"Ошибка сервера {response.status} при запросе {url}"
                            )
                            await asyncio.sleep(
                                self.server_error_backoff
                            )  # Задержка при ошибке сервера
                            return None
                        else:
                            logger.debug(f"Ошибка {response.status} при запросе {url}")
                            return None
                except ClientResponseError as e:
                    logger.error(f"Ошибка HTTP: {e}")
                    await asyncio.sleep(self.server_error_backoff)
                    return None
                except Exception as e:
                    logger.error(f"Неизвестная ошибка при запросе {url}: {e}")
                    return None
        logger.error(f"Не удалось выполнить запрос после {retries} попыток: {url}")
        return None

    async def get_post(self, post_id: int) -> DanbooruPost:
        """Получает пост по его ID."""
        url = f"{self.base_url}/posts/{post_id}.json"
        data = await self._make_request(url)
        if data:
            return DanbooruPost(**data)
        return None

    async def get_popular_posts(
        self, page: int = 1, limit: int = 10
    ) -> List[DanbooruPost]:
        """Получает популярные посты за текущий день."""
        url = f"{self.base_url}/explore/posts/popular.json"
        today = datetime.now().strftime("%Y-%m-%d")
        params = {"date": today, "scale": "day", "page": page, "limit": limit}
        data = await self._make_request(url, params)
        if data and isinstance(data, list):
            return [DanbooruPost(**post) for post in data if isinstance(post, dict)]
        return []

    async def get_hot_posts(self) -> List[DanbooruPost]:
        """Получает горячие посты."""
        url = f"{self.base_url}/posts.json"
        params = {"d": 1, "tags": "order:rank", "limit": 10}
        data = await self._make_request(url, params)
        if data and isinstance(data, list):
            return [DanbooruPost(**post) for post in data if isinstance(post, dict)]
        return []

    async def search_posts(self, tags: str, limit: int = 10) -> List[DanbooruPost]:
        """Ищет посты по тегам с заданным лимитом."""
        url = f"{self.base_url}/posts.json"
        params = {"tags": tags, "limit": limit}
        data = await self._make_request(url, params)
        if data:
            return [DanbooruPost(**post) for post in data]
        return []


class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.semaphore = asyncio.Semaphore(max_calls)
        self.last_reset = asyncio.get_event_loop().time()

    async def acquire(self):
        while True:
            current_time = asyncio.get_event_loop().time()
            time_since_reset = current_time - self.last_reset
            if time_since_reset > self.period:
                self.semaphore = asyncio.Semaphore(self.max_calls)
                self.last_reset = current_time
            if self.semaphore.locked():
                await asyncio.sleep(self.period - time_since_reset)
            else:
                await self.semaphore.acquire()
                break
