import asyncio
from datetime import datetime
from typing import List

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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
        self.semaphore = asyncio.Semaphore(5)
        self.file_size_limit = 1_950_000  # ~1.95 MB

    async def _get_post(self, post_id: int) -> DanbooruPost:
        """Получает пост по его ID."""
        url = f"{self.base_url}/posts/{post_id}.json"
        async with self.http_session() as session:
            async with session.get(url, headers=self.headers) as response:
                data = await response.json()
                return DanbooruPost(**data)

    async def _get_popular_posts(
        self, page: int = 1, limit: int = 10
    ) -> List[DanbooruPost]:
        """Получает популярные посты за текущий день."""
        url = f"{self.base_url}/explore/posts/popular.json"
        today = datetime.now().strftime("%Y-%m-%d")
        params = {"date": today, "scale": "day", "page": page, "limit": limit}
        async with self.http_session() as session:
            async with session.get(
                url, headers=self.headers, params=params
            ) as response:
                data = await response.json()
                return [DanbooruPost(**post) for post in data]

    async def _search_posts(self, tags: str, limit: int = 10) -> List[DanbooruPost]:
        """Ищет посты по тегам с заданным лимитом."""
        url = f"{self.base_url}/posts.json"
        params = {"tags": tags, "limit": limit}
        async with self.semaphore:
            async with self.http_session() as session:
                async with session.get(
                    url, headers=self.headers, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json(content_type="application/json")
                        return [DanbooruPost(**post) for post in data]
                    else:
                        logger.debug(f"Ошибка поиска постов, статус: {response.status}")
                        return []

    async def _get_subscriptions(self) -> List[str] | None:
        """Получает список тегов подписок из базы данных."""
        async with self.database_sessionmaker() as session:
            repo = Repo(session)
            return await repo.get_subscriptions_list()

    async def _filter_new_posts(self, posts: List[DanbooruPost]) -> List[DanbooruPost]:
        """Фильтрует посты, оставляя только те, которых нет в базе данных."""
        async with self.database_sessionmaker() as session:
            repo = Repo(session)
            new_posts = []
            for post in posts or []:
                if await repo.get_post(post.id) is None:
                    new_posts.append(post)
                    await repo.add_post(post.id)
            return new_posts

    async def _get_new_posts_by_tags(self, tags: str) -> List[DanbooruPost]:
        """Получает новые посты по заданным тегам."""
        try:
            last_posts = await self._search_posts(tags=tags)
            new_posts = await self._filter_new_posts(last_posts)
            if new_posts:
                logger.info(f"Найдено {len(new_posts)} новых постов по тегу {tags}")
            return new_posts
        except Exception as e:
            logger.error(f"Ошибка при получении постов по тегу {tags}: {e}")
            raise

    def _get_source_button(self, post: DanbooruPost) -> InlineKeyboardMarkup:
        url = f"https://danbooru.donmai.us/posts/{post.id}"
        button = InlineKeyboardButton(text="Источник", url=url)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
        return keyboard

    def _get_post_caption(self, post: DanbooruPost) -> str:
        """Генерирует подпись для поста с ограничением в 1024 символа."""
        artist = post.tag_string_artist or "Неизвестно"
        character = post.tag_string_character or "Неизвестно"
        copyright = post.tag_string_copyright or "Неизвестно"
        caption = f"<b>Создатель:</b> {artist}\n<b>Персонаж:</b> {character}\n<b>Копирайт:</b> {copyright}"
        return caption[:1024]

    async def _send_posts(self, posts: List[DanbooruPost]) -> None:
        """Отправляет посты в чат администратора."""
        for post in posts:
            if not post.large_file_url:
                continue
            try:
                caption = self._get_post_caption(post)
                keyboard = self._get_source_button(post)
                if post.file_ext in ("jpg", "jpeg", "png", "webp"):
                    await self.telegram_bot.send_photo(
                        chat_id=self.admin_id,
                        photo=post.large_file_url,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard
                    )
                elif post.file_ext in ("mp4", "webm", "zip"):
                    await self.telegram_bot.send_video(
                        chat_id=self.admin_id,
                        video=post.large_file_url,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard
                    )
                elif post.file_ext == "gif":
                    await self.telegram_bot.send_animation(
                        chat_id=self.admin_id,
                        animation=post.large_file_url,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard
                    )
                else:
                    await self.telegram_bot.send_message(
                        self.admin_id,
                        f"{post.large_file_url}\n{caption}\n\n<b>Неподдерживаемый формат файла.</b>",
                        parse_mode=ParseMode.HTML,
                    )
                    logger.debug(f"Неизвестный формат: {post.file_ext}")
            except TelegramBadRequest as e:
                if post.preview_file_url and post.file_size >= self.file_size_limit:
                    await self.telegram_bot.send_photo(
                        chat_id=self.admin_id,
                        photo=post.preview_file_url,
                        caption=f"{post.large_file_url}\n{caption}\n\n"
                        f"<b>Файл слишком большой: {post.file_size / 1_000_000:.2f} МБ</b>",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await self.telegram_bot.send_message(
                        self.admin_id,
                        f"{post.large_file_url}\n{caption}\n\n<b>Ошибка Telegram: {e}</b>",
                        parse_mode=ParseMode.HTML,
                    )
            except Exception as e:
                await self.telegram_bot.send_message(
                    self.admin_id,
                    f"{post.large_file_url}\n{caption}\n\n<b>Ошибка: {e}</b>",
                    parse_mode=ParseMode.HTML,
                )
            await asyncio.sleep(0.1)  # Минимальная задержка для соблюдения лимитов

    async def _get_new_posts(self, subscriptions: List[str]) -> List[DanbooruPost]:
        """Собирает новые посты для всех подписок."""
        tasks = [self._get_new_posts_by_tags(tags) for tags in subscriptions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        posts = []
        for result in results:
            if isinstance(result, list):
                posts.extend(result)
        return posts

    async def check_new_posts(self) -> None:
        """Проверяет наличие новых постов и отправляет их."""
        logger.info("Проверка новых постов")
        subscriptions = await self._get_subscriptions()
        if not subscriptions:
            logger.info("Подписки не найдены")
            return

        new_posts = await self._get_new_posts(subscriptions)
        if new_posts:
            logger.info(f"Найдено {len(new_posts)} новых постов")
            await self._send_posts(new_posts)
        else:
            logger.info("Новые посты не найдены")
        logger.info("Проверка завершена")

    async def check_popular_posts(self) -> None:
        """Проверяет популярные посты и отправляет их."""
        logger.info("Проверка популярных постов")
        posts = await self._get_popular_posts()
        if posts:
            logger.info(f"Найдено {len(posts)} популярных постов")
            await self._send_posts(posts)
        else:
            logger.info("Популярные посты не найдены")
        logger.info("Проверка завершена")
