from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List


class Repo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_subscriptions_list(self) -> List | None:
        # Получение всех подписок
        tags = await self.session.execute(
            text("SELECT DISTINCT tags FROM subscriptions;")
        )
        tags = tags.fetchall()
        if tags:
            tag_list = ["".join(tag) for tag in tags]
            return tag_list
        else:
            return None

    async def add_subscription(self, tags: str) -> bool:
        # добавить tags в подписки
        try:
            await self.session.execute(
                text(f"INSERT INTO subscriptions (tags) VALUES ('{tags}');")
            )
            await self.session.commit()
            logger.info(f"{tags} - добавлено в подписки")
            return True
        except Exception as e:
            logger.debug(e)
            return False

    async def filter_new_posts(self, posts) -> list | None:
        # Фильтрует посты, записывая их в бд и возвращает список ссылок на новые
        if posts:
            new_posts = []
            for post in posts:
                _id = post["id"]
                result = await self.session.execute(
                    text(f"SELECT id FROM posts WHERE id = {_id}")
                )
                result = result.fetchone()
                if result is None:
                    new_posts.append(post)
                    await self.session.execute(
                        text(f"INSERT INTO posts (id) VALUES ({_id})")
                    )
                    await self.session.commit()
            return new_posts
        else:
            return None

    async def delete_sub(self, tags: str) -> bool:
        # Удаляет запись
        result = await self.session.execute(
            text(f"SELECT * FROM subscriptions WHERE tags = '{tags}';")
        )
        result = result.fetchone()
        if result:
            await self.session.execute(
                text(f"DELETE FROM subscriptions WHERE tags = '{tags}';")
            )
            await self.session.commit()
            logger.info(f"{tags} -  удалено")
            return True
        else:
            logger.info(f"{tags} - не найдено")
            return False