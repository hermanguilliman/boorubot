from asyncio import sleep

from aiogram import Bot
from loguru import logger
from pybooru import Danbooru
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.repository import Repo


async def get_new_posts_by_tags(danbooru, repo: Repo, tags: str = None) -> list | None:
    """
    Принимает тэги и возвращает список постов
    """
    if tags is None:
        return None

    last_posts = danbooru.post_list(tags=tags, limit=10)
    new_posts = await repo.filter_new_posts(posts=last_posts)
    return new_posts


async def create_session(async_sessionmaker: async_sessionmaker[AsyncSession]):
    async with async_sessionmaker() as session:
        return session


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
    subscriptions = await repo.get_subscriptions_list()
    new_posts = []

    try:
        if subscriptions:
            # Получаем новые посты по каждому набору тэгов
            for sub in subscriptions:
                posts = await get_new_posts_by_tags(danbooru, repo, sub)
                if posts:
                    for post in posts:
                        new_posts.append(post)

        if len(new_posts) > 0:
            # Если есть список новых постов

            for post in new_posts:
                if "file_url" in post:
                    caption = f"<b>Автор:</b> {post['tag_string_artist']}\
                        \n<b>Персонаж:</b> {post['tag_string_character']}\
                        \n<b>Теги:</b> {post['tag_string_general']}"
                    if post["file_ext"] in ("jpg", "jpeg", "png", "webp"):
                        await bot.send_photo(
                            chat_id=admin_id,
                            photo=post["file_url"],
                            caption=caption,
                            parse_mode="HTML",
                        )
                    elif post["file_ext"] in ("mp4", "webm"):
                        await bot.send_video(
                            chat_id=admin_id,
                            video=post["file_url"],
                            caption=caption,
                            parse_mode="HTML",
                        )
                    elif post["file_ext"] == "gif":
                        await bot.send_animation(
                            chat_id=admin_id,
                            animation=post["file_url"],
                            caption=caption,
                            parse_mode="HTML",
                        )
                    else:
                        logger.debug(
                            f"Не знаю что делать с форматом {post['file_ext']}"
                        )
                    await sleep(1)
        else:
            logger.info("Новые сообщения не найдены")
    except Exception as e:
        await bot.send_message(admin_id, f"Возникла ошибка: \n {e}")
