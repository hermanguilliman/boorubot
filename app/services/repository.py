from typing import Optional

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.posts import Post
from app.models.subscriptions import Subscription


class Repo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_subscriptions_list(self) -> Optional[list[tuple[int, str]]]:
        result = await self.session.execute(
            select(Subscription.id, Subscription.tags)
        )
        subs = result.all()
        return subs or None

    async def get_existing_post_ids(self, post_ids: list[int]) -> set[int]:
        """Batch-проверка существующих постов."""
        if not post_ids:
            return set()
        result = await self.session.execute(
            select(Post.id).where(Post.id.in_(post_ids))
        )
        return {row[0] for row in result.all()}

    async def add_posts_batch(self, post_ids: list[int]) -> int:
        """Batch-вставка с ON CONFLICT DO NOTHING."""
        if not post_ids:
            return 0
        try:
            stmt = insert(Post).values([{"id": pid} for pid in post_ids])
            stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount or 0
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Batch insert failed: {e}")
            return 0

    async def get_post(self, post_id: int) -> Optional[Post]:
        return await self.session.get(Post, post_id)

    async def add_post(self, post_id: int) -> bool:
        try:
            self.session.add(Post(id=post_id))
            await self.session.commit()
            return True
        except IntegrityError:
            await self.session.rollback()
            return False

    async def add_subscription(self, tags: str) -> bool:
        try:
            self.session.add(Subscription(tags=tags))
            await self.session.commit()
            return True
        except IntegrityError:
            await self.session.rollback()
            return False

    async def delete_sub(self, sub_id: int) -> Optional[str]:
        try:
            result = await self.session.execute(
                select(Subscription.tags).where(Subscription.id == sub_id)
            )
            tag = result.scalar_one_or_none()
            if tag is None:
                return None

            await self.session.execute(
                delete(Subscription).where(Subscription.id == sub_id)
            )
            await self.session.commit()
            return tag
        except Exception:
            await self.session.rollback()
            return None
