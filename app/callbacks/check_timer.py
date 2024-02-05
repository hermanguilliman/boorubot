from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram.types import CallbackQuery


async def on_check_timer(callback: CallbackQuery, button: Button,
                    manager: DialogManager):
    await callback.answer("Таймер обновлён!")
