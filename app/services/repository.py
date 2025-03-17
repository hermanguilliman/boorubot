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

    async def get_subscriptions_list(self) -> List[tuple[int, str]] | None:
        """Получает список всех подписок с их ID и тегами."""
        stmt = select(Subscription.id, Subscription.tags)
        result = await self.session.execute(stmt)
        subscriptions = result.all()  # Возвращает список кортежей (id, tag)
        return subscriptions or None

    async def get_post(self, id: int) -> Post | None:
        """Получает пост по ID."""
        return await self.session.get(Post, id)

    async def add_post(self, id: int) -> bool:
        """Добавляет пост в базу данных."""
        try:
            post = Post(id=id)
            self.session.add(post)
            await self.session.commit()
            return True
        except exc.IntegrityError:
            await self.session.rollback()
            logger.debug(f"Пост с ID {id} уже существует")
            return False
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при добавлении поста {id}: {e}")
            return False

    async def add_subscription(self, tags: str) -> bool:
        """Добавляет подписку в базу данных."""
        try:
            sub = Subscription(tags=tags)
            self.session.add(sub)
            await self.session.commit()
            logger.info(f"Подписка на {tags} добавлена")
            return True
        except exc.IntegrityError:
            await self.session.rollback()
            logger.debug(f"Подписка на {tags} уже существует")
            return False
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при добавлении подписки {tags}: {e}")
            return False

    async def delete_sub(self, sub_id: int) -> str | None:
        """Удаляет подписку по ID и возвращает её тег."""
        try:
            # Получаем тег подписки
            stmt = select(Subscription.tags).where(Subscription.id == sub_id)
            result = await self.session.execute(stmt)
            tag = result.scalar_one_or_none()

            if tag is None:
                return None

            # Удаляем подписку
            delete_stmt = delete(Subscription).where(Subscription.id == sub_id)
            await self.session.execute(delete_stmt)
            await self.session.commit()
            return tag
        except Exception:
            await self.session.rollback()
            return None
