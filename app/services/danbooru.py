import asyncio
from typing import Callable

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.danbooru_client import DanbooruAPI
from app.models.danbooru import DanbooruPost
from app.services.repository import Repo


class DanbooruService:
    def __init__(
        self,
        session_pool: async_sessionmaker[AsyncSession],
        bot: Bot,
        admin_id: int,
    ):
        self.session_pool = session_pool
        self.telegram_bot = bot
        self.admin_id = admin_id
        self.file_size_limit = 1_950_000
        self.api = DanbooruAPI()
        self._send_delay = 0.3

    async def close(self) -> None:
        await self.api.close()

    async def _notify_admin(self, message: str) -> None:
        try:
            await self.telegram_bot.send_message(
                self.admin_id, message, parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

    async def _filter_new_posts(
        self, posts: list[DanbooruPost]
    ) -> list[DanbooruPost]:
        """Фильтрует посты batch-запросом."""
        if not posts:
            return []

        async with self.session_pool() as session:
            repo = Repo(session)
            post_ids = [p.id for p in posts]
            existing_ids = await repo.get_existing_post_ids(post_ids)

            new_posts = [p for p in posts if p.id not in existing_ids]

            if new_posts:
                await repo.add_posts_batch([p.id for p in new_posts])

            return new_posts

    @staticmethod
    def _get_keyboard(post: DanbooruPost) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Источник",
                        url=f"https://danbooru.donmai.us/posts/{post.id}",
                    )
                ]
            ]
        )

    @staticmethod
    def _get_caption(post: DanbooruPost) -> str:
        return (
            f"<b>Создатель:</b> {post.tag_string_artist or 'Неизвестно'}\n"
            f"<b>Персонаж:</b> {post.tag_string_character or 'Неизвестно'}\n"
            f"<b>Копирайт:</b> {post.tag_string_copyright or 'Неизвестно'}"
        )[:1024]

    async def _send_post(self, post: DanbooruPost) -> None:
        if not post.large_file_url:
            return

        caption = self._get_caption(post)
        keyboard = self._get_keyboard(post)

        ext_to_method = {
            ("jpg", "jpeg", "png", "webp"): ("send_photo", "photo"),
            ("mp4", "webm", "zip"): ("send_video", "video"),
            ("gif",): ("send_animation", "animation"),
        }

        try:
            for extensions, (method_name, param_name) in ext_to_method.items():
                if post.file_ext in extensions:
                    method = getattr(self.telegram_bot, method_name)
                    await method(
                        chat_id=self.admin_id,
                        **{param_name: post.large_file_url},
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard,
                    )
                    return

            # Неизвестный формат
            await self.telegram_bot.send_message(
                self.admin_id,
                f"{post.large_file_url}\n{caption}\n\n"
                f"<b>Формат не поддерживается: {post.file_ext}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except TelegramBadRequest:
            await self._send_fallback(post, caption, keyboard)
        except Exception as e:
            logger.error(f"Failed to send post {post.id}: {e}")

    async def _send_fallback(
        self, post: DanbooruPost, caption: str, keyboard: InlineKeyboardMarkup
    ) -> None:
        """Отправка превью при ошибке."""
        if post.preview_file_url and post.file_size >= self.file_size_limit:
            await self.telegram_bot.send_photo(
                chat_id=self.admin_id,
                photo=post.preview_file_url,
                caption=f"{post.large_file_url}\n{caption}\n\n"
                f"<b>Файл: {post.file_size / 1_000_000:.2f} МБ</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:
            await self.telegram_bot.send_message(
                self.admin_id,
                f"{post.large_file_url}\n{caption}",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

    async def _send_posts(self, posts: list[DanbooruPost]) -> None:
        for post in posts:
            await self._send_post(post)
            await asyncio.sleep(self._send_delay)

    async def _collect_new_posts(
        self, tags_list: list[str]
    ) -> list[DanbooruPost]:
        """Собирает посты с дедупликацией."""
        tasks = [self.api.search_posts(tags) for tags in tags_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_posts: dict[int, DanbooruPost] = {}
        for result in results:
            if isinstance(result, list):
                for post in result:
                    all_posts.setdefault(post.id, post)

        return await self._filter_new_posts(list(all_posts.values()))

    async def check_new_posts(self) -> None:
        logger.info("Checking new posts")

        async with self.session_pool() as session:
            subs = await Repo(session).get_subscriptions_list()

        if not subs:
            logger.info("No subscriptions")
            return

        new_posts = await self._collect_new_posts([s[1] for s in subs])

        if new_posts:
            logger.info(f"Found {len(new_posts)} new posts")
            await self._send_posts(new_posts)

    async def _check_posts_generic(
        self,
        fetch: Callable,
        name: str,
    ) -> None:
        """Универсальный метод проверки."""
        logger.info(f"Checking {name} posts")
        posts = await fetch()

        if posts is None:
            await self._notify_admin(
                f"<b>Ошибка:</b> Сервер недоступен ({name})"
            )
            return

        if posts:
            logger.info(f"Found {len(posts)} {name} posts")
            await self._send_posts(posts)

    async def check_popular_posts(self) -> None:
        await self._check_posts_generic(
            lambda: self.api.get_popular_posts(limit=20), "popular"
        )

    async def check_hot_posts(self) -> None:
        await self._check_posts_generic(
            lambda: self.api.get_hot_posts(limit=20), "hot"
        )
