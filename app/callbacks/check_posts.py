from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from app.services.danbooru import DanbooruService


async def on_popular_click(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    danbooru: DanbooruService = manager.middleware_data.get("danbooru")
    await danbooru.check_popular_posts()
    await callback.answer("🚀 Получены популярные посты")


async def on_hot_click(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    danbooru: DanbooruService = manager.middleware_data.get("danbooru")
    await danbooru.check_hot_posts()
    await callback.answer("🌶 Получены горячие посты")
