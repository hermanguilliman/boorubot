from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import ChatEvent, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button

from app.services.repository import Repo
from app.states.danmenu import DanMenu


async def on_select_sub(
    callback: ChatEvent, select: Any, manager: DialogManager, item_id: str
):
    manager.dialog_data["sub_to_delete"] = int(item_id)
    await manager.switch_to(state=DanMenu.delete)


async def on_delete_confirm(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    repo: Repo = manager.middleware_data.get("repo")
    sub_id = manager.dialog_data.get("sub_to_delete")
    tag = await repo.delete_sub(sub_id=int(sub_id))
    if tag:
        await callback.message.answer(
            f"<b>👌 Подписка '{tag}' успешно удалена!</b>", parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            f"<b>❌ Подписка с ID {sub_id} не найдена.</b>", parse_mode="HTML"
        )
    await manager.done()
    await manager.start(DanMenu.main, mode=StartMode.RESET_STACK)
