import asyncio
from datetime import datetime
from typing import Optional

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from loguru import logger

from app.models.danbooru import DanbooruPost


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.tokens = float(max_calls)
        self.last_update: Optional[float] = None
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()

            if self.last_update is not None:
                elapsed = now - self.last_update
                self.tokens = min(
                    self.max_calls,
                    self.tokens + elapsed * (self.max_calls / self.period),
                )

            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (self.period / self.max_calls)
                await asyncio.sleep(wait_time)
                self.tokens = 0
                self.last_update = loop.time()
            else:
                self.tokens -= 1


class DanbooruAPI:
    def __init__(self):
        self.base_url = "https://danbooru.donmai.us"
        self.rate_limiter = RateLimiter(max_calls=5, period=1)
        self.server_error_backoff = 60
        self._session: Optional[ClientSession] = None

    async def _get_session(self) -> ClientSession:
        """Возвращает переиспользуемую сессию."""
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                headers={"Content-Type": "application/json"},
                timeout=ClientTimeout(total=30),
                connector=TCPConnector(limit=10),
            )
        return self._session

    async def close(self) -> None:
        """Закрывает HTTP-сессию."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _make_request(
        self, url: str, params: Optional[dict] = None
    ) -> Optional[dict | list]:
        """Выполняет HTTP-запрос с retry."""
        retries = 3
        session = await self._get_session()

        for attempt in range(retries):
            await self.rate_limiter.acquire()
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()

                    if response.status == 429:
                        wait_time = 2**attempt
                        logger.debug(f"Rate limited, retry in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status >= 500:
                        logger.error(f"Server error {response.status}: {url}")
                        if attempt < retries - 1:
                            await asyncio.sleep(self.server_error_backoff)
                            continue
                        return None

                    logger.debug(f"Error {response.status}: {url}")
                    return None

            except asyncio.TimeoutError:
                logger.error(f"Timeout: {url}")
                if attempt < retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
            except Exception as e:
                logger.error(f"Request error {url}: {e}")
                return None

        logger.error(f"Failed after {retries} attempts: {url}")
        return None

    def _parse_posts(
        self, data: Optional[list]
    ) -> Optional[list[DanbooruPost]]:
        """Парсит список постов."""
        if data is None:
            return None
        if isinstance(data, list):
            return [
                DanbooruPost(**post) for post in data if isinstance(post, dict)
            ]
        return []

    async def get_post(self, post_id: int) -> Optional[DanbooruPost]:
        url = f"{self.base_url}/posts/{post_id}.json"
        data = await self._make_request(url)
        if data and isinstance(data, dict):
            return DanbooruPost(**data)
        return None

    async def get_popular_posts(
        self, page: int = 1, limit: int = 10
    ) -> Optional[list[DanbooruPost]]:
        url = f"{self.base_url}/explore/posts/popular.json"
        params = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "scale": "day",
            "page": page,
            "limit": limit,
        }
        return self._parse_posts(await self._make_request(url, params))

    async def get_hot_posts(
        self, limit: int = 10
    ) -> Optional[list[DanbooruPost]]:
        url = f"{self.base_url}/posts.json"
        params = {"d": 1, "tags": "order:rank", "limit": limit}
        return self._parse_posts(await self._make_request(url, params))

    async def search_posts(
        self, tags: str, limit: int = 10
    ) -> Optional[list[DanbooruPost]]:
        url = f"{self.base_url}/posts.json"
        params = {"tags": tags, "limit": limit}
        return self._parse_posts(await self._make_request(url, params))
