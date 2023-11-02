from aiogram.filters import CommandObject
from aiogram.types import Message
from loguru import logger
from asyncio import sleep
from app.services.repo import Repo


async def delete_sub(message: Message, command: CommandObject, repo: Repo):
    if command.args:
        await message.answer(f"Удаляю {command.args}...")
        await sleep(.5)
        if repo.delete_sub(command.args):
            logger.info(f"{command.args} -  удалено из подписок")
            await message.answer(f"✅ <b>{command.args} -  удалено из подписок</b>")
        else:
            logger.info(f"Не получилось удалить {command.args}")
            await message.answer(f"<b>❌ Не получилось удалить {command.args}</b>")
    else:
        await message.answer("Используйте <b>/del tag</b> чтобы удалить подписку")