from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_default_commands(bot: Bot):
    commands = [
        BotCommand(
            command="start",
            description="Начало",
        ),
        BotCommand(
            command="add",
            description="Добавить подписку (указать какую)",
        ),
        BotCommand(
            command="del",
            description="Удалить подписку (указать какую)",
        ),
        BotCommand(command="subs", description="Показать все активные подписки"),
    ]

    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())
