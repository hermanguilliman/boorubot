from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram.types import CallbackQuery
from app.services.danbooru import DanbooruService


async def on_popular_click(callback: CallbackQuery, button: Button,
                    manager: DialogManager):
    danbooru: DanbooruService = manager.middleware_data.get("danbooru")
    await danbooru.check_popular_posts()

