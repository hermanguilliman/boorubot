from aiogram_dialog import DialogManager

from app.services.repository import Repo


async def get_subscribes(dialog_manager: DialogManager, **kwargs):
    repo: Repo = dialog_manager.dialog_data.get("repo")
    subs = await repo.get_subscriptions_list()
    return {
        "tags": subs,
    }
