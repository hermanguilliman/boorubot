import asyncio
from datetime import datetime
from typing import List

from aiogram import Bot
from aiogram.enums import ParseMode
from aiohttp import ClientSession
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.danbooru import DanbooruPost
from app.services.repository import Repo


class DanbooruService:
    def __init__(
        self,
        async_sessionmaker: async_sessionmaker[AsyncSession],
        bot: Bot,
        admin_id: int,
    ):
        self.base_url = "https://danbooru.donmai.us"
        self.headers = {"Content-Type": "application/json"}
        self.http_session = ClientSession
        self.database_sessionmaker = async_sessionmaker
        self.telegram_bot = bot
        self.admin_id = admin_id
        self.semaphore = asyncio.Semaphore(10)

    async def _get_post(self, post_id):
        url = f"{self.base_url}/posts/{post_id}.json"
        async with self.http_session() as session:
            async with session.get(url, headers=self.headers) as response:
                data = await response.json()
                return DanbooruPost(**data)


    async def _get_popular_posts(self):
        url = f"{self.base_url}/explore/posts/popular.json"
        today = datetime.now().strftime("%Y-%m-%d")
        params = {"date": today, "scale": "day", "page": 1}
        async with self.http_session() as session:
            async with session.get(
                url, headers=self.headers, params=params
            ) as response:
                data = await response.json()
                return [DanbooruPost(**post) for post in data]

    async def _search_posts(self, tags: str, limit=10):
        url = f"{self.base_url}/posts.json"
        params = {"tags": tags, "limit": limit}
        async with self.semaphore:
            async with self.http_session() as session:
                async with session.get(
                    url=url, headers=self.headers, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json(content_type="application/json")
                        return [DanbooruPost(**post) for post in data]
                    else:
                        logger.debug(f"Response status: {response.status}")

    async def _get_subscriptions(self) -> List | None:
        async with self.database_sessionmaker() as session:
            repo = Repo(session)
            subscriptions = await repo.get_subscriptions_list()
            return subscriptions

    async def _filter_new_posts(
        self, posts: List[DanbooruPost]
    ) -> List[DanbooruPost] | None:
        # Фильтрует посты, записывая их в бд и возвращает список ссылок на новые
        async with self.database_sessionmaker() as session:
            repo = Repo(session)
            if posts:
                new_posts = []
                for post in posts:
                    result = await repo.get_post(post.id)
                    if result is None:
                        new_posts.append(post)
                        await repo.add_post(post.id)
                return new_posts
            else:
                return None

    async def _get_new_posts_by_tags(
        self, tags: str = None
    ) -> List[DanbooruPost] | None:
        """
        Возвращает посты, которые еще не были отправлены
        """
        try:
            if tags:
                last_posts = await self._search_posts(tags=tags)
                new_posts = await self._filter_new_posts(posts=last_posts)

                if new_posts:
                    logger.info(f"Получено {len(new_posts)} постов, по тегу {tags}")
                    return new_posts
            else:
                return None
        except Exception as e:
            logger.error(e)

    @staticmethod
    def _short_caption(caption: str) -> str:
        if len(caption) > 1024:
            caption = caption[:1024]
        return caption

    def _get_post_caption(self, post: DanbooruPost) -> str:
        """
        Создает подпись для поста
        """
        caption = f"<b>Создатель:</b> {post.tag_string_artist}\n<b>Персонаж:</b> {post.tag_string_character}\n<b>Копирайт:</b> {post.tag_string_copyright}"
        caption = DanbooruService._short_caption(caption)
        return caption

    async def _send_new_posts(self, new_posts: List[DanbooruPost]):
        """
        Отправляет новые посты в чат администратора
        """
        for post in new_posts:
            if hasattr(post, "large_file_url"):
                try:
                    caption = self._get_post_caption(post)
                    if post.file_ext in ("jpg", "jpeg", "png", "webp"):
                        await self.telegram_bot.send_photo(
                            chat_id=self.admin_id,
                            photo=post.large_file_url,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                        )
                    elif post.file_ext in ("mp4", "webm"):
                        await self.telegram_bot.send_video(
                            chat_id=self.admin_id,
                            video=post.large_file_url,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                        )
                    elif post.file_ext == "gif":
                        await self.telegram_bot.send_animation(
                            chat_id=self.admin_id,
                            animation=post.large_file_url,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                        )
                    else:
                        logger.debug(f"Не знаю что делать с форматом {post.file_ext}")
                except Exception as e:
                    await self.telegram_bot.send_message(
                        self.admin_id,
                        f"{post.large_file_url}\n{caption}\n\nПроизошла ошибка:\n{e}",
                        parse_mode=ParseMode.HTML,
                    )
                await asyncio.sleep(1)

    async def _get_new_posts(self, subscriptions: List) -> List[DanbooruPost]:
        """
        Получает новые посты для каждой подписки
        """
        tasks = []

        for tags in subscriptions:
            tasks.append(asyncio.create_task(self._get_new_posts_by_tags(tags=tags)))

        results = await asyncio.gather(*tasks)
        results = list(filter(lambda x: x is not None, results))
        posts = [post for posts in results for post in posts if post is not None]
        return posts

    async def check_new_posts(self):
        """
        Получаем свежие посты
        """
        logger.info("Проверка новых сообщений")

        subscriptions = await self._get_subscriptions()

        if subscriptions:
            new_posts: List[DanbooruPost] = await self._get_new_posts(subscriptions)

            if len(new_posts) > 0:
                await self._send_new_posts(new_posts)
            else:
                logger.info("Новые посты не найдены")
        else:
            logger.info("Подписки не найдены")
        logger.info("Проверка закончена")

    async def check_popular_posts(self):
        posts = await self._get_popular_posts()
        if posts:
            if len(posts) > 0:
                await self._send_new_posts(posts)
