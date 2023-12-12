from typing import Any

from aiogram_dialog import ChatEvent, DialogManager, StartMode

from app.services.repository import Repo
from app.states.danmenu import DanMenu


async def on_subscibe_deleted(
    callback: ChatEvent, select: Any, manager: DialogManager, item_id: str
):
    repo: Repo = manager.middleware_data.get("repo")
    await repo.delete_sub(tags=item_id)
    await callback.message.answer(
        f"<b>👌 Подписка {item_id} успешно удалена!</b>", parse_mode="HTML"
    )
    await manager.done()
    await manager.start(DanMenu.main, mode=StartMode.RESET_STACK)
