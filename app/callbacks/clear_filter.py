from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button


async def on_clear_filter(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    del manager.dialog_data["search_query"]
    await callback.answer("🧹 Поисковый фильтр очищен!")
    await manager.update({})
