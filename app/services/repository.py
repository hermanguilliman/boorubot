from typing import List

from loguru import logger
from sqlalchemy import delete, exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.posts import Post
from app.models.subscriptions import Subscription


class Repo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_subscriptions_list(self) -> List[str] | None:
        # Получение всех подписок
        stmt = select(Subscription.tags)
        result = await self.session.execute(stmt)
        tag_list = result.scalars().all()
        if tag_list:
            return tag_list
        else:
            return None

    async def get_post(self, id: int) -> Post | None:
        return await self.session.get(Post, id)

    async def add_post(self, id: int) -> bool:
        try:
            post = Post(id=id)
            self.session.add(post)
            await self.session.commit()
            return True
        except exc.IntegrityError:
            await self.session.rollback()
            print("Запись уже существует!")
            return False
        except Exception as e:
            await self.session.rollback()
            logger.debug(f"Произошла ошибка при добавлении записи: {str(e)}")
            return False

    async def add_subscription(self, tags: str) -> bool:
        # добавить tags в подписки
        try:
            sub = Subscription(tags=tags)
            self.session.add(sub)
            await self.session.commit()
            logger.info(f"{tags} - добавлено в подписки")
            return True
        except exc.IntegrityError:
            await self.session.rollback()
            print("Запись уже существует!")
            return False
        except Exception as e:
            await self.session.rollback()
            logger.debug(f"Произошла ошибка при добавлении записи: {str(e)}")
            return False

    async def delete_sub(self, tags: str) -> bool:
        # Удаляет запись
        stmt = delete(Subscription).where(Subscription.tags == tags)
        await self.session.execute(stmt)
        await self.session.commit()
        return True
