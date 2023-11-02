from aiogram import types
from asyncio import sleep


async def start(message: types.Message):
    await message.answer("Привет, я booru бот!")
    await sleep(0.7)
    await message.answer(
        """<b>Я могу следить за обновления твоих любимых Danbooru тэгов\n
        /add tag Добавить тэг в подписки\n
        /subs Посмотреть подписки\n
        /del tag Удалить подписку</b>
    """
    )