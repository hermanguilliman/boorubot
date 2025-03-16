from typing import Any

from aiogram_dialog import ChatEvent, DialogManager, StartMode

from app.services.repository import Repo
from app.states.danmenu import DanMenu


async def on_subscibe_deleted(
    callback: ChatEvent, select: Any, manager: DialogManager, item_id: str
):
    repo: Repo = manager.middleware_data.get("repo")
    sub_id = int(item_id)  # Преобразуем строку в число
    tag = await repo.delete_sub(sub_id=sub_id)
    
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
