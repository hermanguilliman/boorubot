from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_default_commands(bot: Bot):
    commands = [
        BotCommand(
            command="start",
            description="Меню",
        ),
    ]

    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())
