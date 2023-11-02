from aiogram.filters import CommandObject
from aiogram.types import Message
from loguru import logger

from app.services.repo import Repo


async def add_sub(message: Message, command: CommandObject, repo: Repo):
    if command.args:
        if await repo.add_subscription(command.args):
            logger.info(f"{command.args} добавлен в подписки")
            await message.answer(f"<b>✅ {command.args} - подписка добавлена!</b>")
        else:
            logger.info(f"{command.args} не добавлен в подписки")
            await message.answer(
                f"<b>❌ Не получилось добавить {command.args} в базу ❌</b>"
            )
    else:
        await message.answer("<b>❌ Нужно указать тэг или тэги для подписки ❌</b>")
