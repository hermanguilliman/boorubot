import asyncio
from datetime import datetime
from typing import List
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
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
        self.headers = {
            "Content-Type": "application/json",
        }
        self.http_session = ClientSession
        self.database_sessionmaker = async_sessionmaker
        self.telegram_bot = bot
        self.admin_id = admin_id
        self.semaphore = asyncio.Semaphore(5)
        self.file_size_limit = 1950000

    async def _get_post(self, post_id):
        url = f"{self.base_url}/posts/{post_id}.json"
        async with self.http_session() as session:
            async with session.get(url, headers=self.headers) as response:
                data = await response.json()
                return DanbooruPost(**data)

    async def _get_popular_posts(
        self, page: int = 1, limit: int = 10
    ) -> List[DanbooruPost]:
        url = f"{self.base_url}/explore/posts/popular.json"
        today = datetime.now().strftime("%Y-%m-%d")
        params = {
            "date": today,
            "scale": "day",
            "page": page,
            "limit": limit,
        }
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
            await asyncio.sleep(0.5)
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

    def _get_post_caption(self, post: DanbooruPost) -> str:
        artist = post.tag_string_artist if post.tag_string_artist else "Неизвестно"
        character = (
            post.tag_string_character if post.tag_string_character else "Неизвестно"
        )
        copyright = (
            post.tag_string_copyright if post.tag_string_copyright else "Неизвестно"
        )
        caption = (
            f"<b>Создатель:</b> {artist}\n"
            f"<b>Персонаж:</b> {character}\n"
            f"<b>Копирайт:</b> {copyright}"
        )
        return caption[:1024]

    async def _send_new_posts(self, new_posts: List[DanbooruPost]):
        """
        Отправляет новые посты в чат администратора
        """
        for post in new_posts:
            if post.large_file_url:
                try:
                    caption = self._get_post_caption(post)
                    if post.file_ext in ("jpg", "jpeg", "png", "webp"):
                        await self.telegram_bot.send_photo(
                            chat_id=self.admin_id,
                            photo=post.large_file_url,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                        )
                    elif post.file_ext in ("mp4", "webm", "zip"):
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
                        await self.telegram_bot.send_message(
                            self.admin_id,
                            f"{post.large_file_url}\n{caption}\n\n<b>Я не умею работать с этим файлом.</b>",
                            parse_mode=ParseMode.HTML,
                        )
                        logger.debug(f"Не знаю что делать с форматом {post.file_ext}")
                except TelegramBadRequest:
                    if post.preview_file_url:
                        await self.telegram_bot.send_photo(
                            chat_id=self.admin_id,
                            photo=post.preview_file_url,
                            caption=f"{post.large_file_url}\n{caption}\n\n<b>Этот файл слишком большой! {post.file_size/1000000:.2f} мегабайт</b>",
                            parse_mode=ParseMode.HTML,
                        )
                    else:
                        await self.telegram_bot.send_message(
                            chat_id=self.admin_id,
                            text=f"{post.large_file_url}\n{caption}\n\n<b>Этот файл слишком большой! {post.file_size/1000000:.2f} мегабайт</b>",
                            parse_mode=ParseMode.HTML,
                        )

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

    async def _send_popular_posts(self, posts: List[DanbooruPost]):
        if posts:
            mg = MediaGroupBuilder()
            for post in posts:
                if (
                    post.large_file_url
                    and post.file_size < self.file_size_limit
                    and post.file_ext
                    in (
                        "jpg",
                        "jpeg",
                        "png",
                        "webp",
                    )
                ):
                    caption = self._get_post_caption(post=post)
                    mg.add_photo(
                        media=post.large_file_url, caption=caption, parse_mode="HTML"
                    )
                elif (
                    post.large_file_url
                    and post.file_size < self.file_size_limit
                    and post.file_ext in ("mp4", "webm", "zip")
                ):
                    mg.add_video(
                        media=post.large_file_url, caption=caption, parse_mode="HTML"
                    )
            await self.telegram_bot.send_media_group(self.admin_id, media=mg.build())

    async def check_popular_posts(self):
        posts = await self._get_popular_posts()
        if posts:
            if len(posts) > 0:
                await self._send_popular_posts(posts)
