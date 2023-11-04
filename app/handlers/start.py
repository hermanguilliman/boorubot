from aiogram import types
from aiogram_dialog import DialogManager, StartMode

from app.states.danmenu import DanMenu


async def start(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(DanMenu.main, mode=StartMode.RESET_STACK)
