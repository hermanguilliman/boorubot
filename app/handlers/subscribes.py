from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import MessageInput

from app.services.repository import Repo
from app.states.danmenu import DanMenu


async def add_new_subscribe(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    repo: Repo = manager.middleware_data.get("repo")
    tags = message.text
    result = await repo.add_subscription(tags)
    if result:
        await message.answer(
            f"<b>✅ {tags} - успешно добавлено!</b>", parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(
            f"<b>💡 {tags}? Такая запись уже есть!</b>",
            parse_mode=ParseMode.HTML,
        )

    await manager.start(DanMenu.main, mode=StartMode.RESET_STACK)


async def search_subscribes(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    tags = message.text
    manager.dialog_data["search_query"] = tags
