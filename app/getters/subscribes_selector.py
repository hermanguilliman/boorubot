from aiogram_dialog import DialogManager

from app.services.repository import Repo


async def get_subscribes(dialog_manager: DialogManager, **kwargs):
    repo: Repo = dialog_manager.middleware_data.get("repo")
    subscriptions = await repo.get_subscriptions_list()
    return {
        "subscriptions": subscriptions,
    }
