from asyncio import sleep
from typing import List

from aiogram import Bot
from aiogram.enums import ParseMode
from loguru import logger
from pybooru import Danbooru
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.repository import Repo


def short_caption(caption: str) -> str:
    if len(caption) > 1024:
        caption = caption[:1024]
    return caption


async def create_session(async_sessionmaker: async_sessionmaker[AsyncSession]):
    async with async_sessionmaker() as session:
        return session


async def get_new_posts_by_tags(danbooru, repo: Repo, tags: str = None) -> List | None:
    """
    Возвращает посты, которые еще не были отправлены
    """
    if tags:
        last_posts = danbooru.post_list(tags=tags, limit=10)
        new_posts = await repo.filter_new_posts(posts=last_posts)
        if len(new_posts) > 0:
            logger.info(f"Получено {len(new_posts)} постов, по тегу {tags}")
            return new_posts
    else:
        return None


async def check_new_posts(
    bot: Bot,
    async_sessionmaker: async_sessionmaker[AsyncSession],
    danbooru: Danbooru,
    admin_id: int,
):
    """
    Получаем список подписок, проверяем обновления для каждого элемента
    и отправляем новые посты в чат
    """

    session = await create_session(async_sessionmaker)
    repo = Repo(session)
    logger.info("Проверка новых сообщений")

    subscriptions = await get_subscriptions(repo)

    if subscriptions:
        new_posts = await get_new_posts(danbooru, repo, subscriptions)

        if len(new_posts) > 0:
            await send_new_posts(bot, admin_id, new_posts)
        else:
            logger.info("Новые посты не найдены")
    else:
        logger.info("Подписки не найдены")


async def get_subscriptions(repo: Repo) -> List | None:
    """
    Получает список подписок из репозитория
    """
    subscriptions = await repo.get_subscriptions_list()
    return subscriptions


async def get_new_posts(
    danbooru: Danbooru, repo: Repo, subscriptions: List
) -> List[dict]:
    """
    Получает новые посты для каждой подписки
    """
    new_posts = []
    for sub in subscriptions:
        posts = await get_new_posts_by_tags(danbooru, repo, sub)
        if posts:
            new_posts.extend(posts)
    return new_posts


async def send_new_posts(bot: Bot, admin_id: int, new_posts: List[dict]):
    """
    Отправляет новые посты в чат администратора
    """
    for post in new_posts:
        if "file_url" in post:
            url = post["file_url"]
            try:
                caption = get_post_caption(post)
                if post["file_ext"] in ("jpg", "jpeg", "png", "webp"):
                    await bot.send_photo(
                        chat_id=admin_id,
                        photo=url,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                    )
                elif post["file_ext"] in ("mp4", "webm"):
                    await bot.send_video(
                        chat_id=admin_id,
                        video=url,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                    )
                elif post["file_ext"] == "gif":
                    await bot.send_animation(
                        chat_id=admin_id,
                        animation=url,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    logger.debug(f"Не знаю что делать с форматом {post['file_ext']}")
                await sleep(2)
            except Exception as e:
                await bot.send_message(
                    admin_id,
                    f"При отправке {url}\nпроизошла ошибка:\n{e}",
                    parse_mode=None,
                )


def get_post_caption(post: dict) -> str:
    """
    Создает подпись для поста
    """
    caption = f"<b>Создатель:</b> {post['tag_string_artist']}\n<b>Персонаж:</b> {post['tag_string_character']}\n<b>Теги:</b> {post['tag_string_general']}"
    caption = short_caption(caption)
    return caption
