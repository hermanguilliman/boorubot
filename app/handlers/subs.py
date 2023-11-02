from asyncio import sleep

from aiogram.types import Message
from loguru import logger

from app.services.repo import Repo


async def show_subs(message: Message, repo: Repo):
    subs = await repo.get_subscriptions_list()
    if len(subs) > 0:
        await message.answer(f"<b>Активных подписок: {len(subs)}</b>")
        await sleep(0.5)
        await message.answer(", ".join(subs))
    else:
        logger.info("Подписки не найдены")
        await message.answer("<b>Подписки не найдены</b>")
