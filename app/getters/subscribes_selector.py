from aiogram_dialog import DialogManager

from app.services.repository import Repo


async def get_subscribes(dialog_manager: DialogManager, **kwargs):
    repo: Repo = dialog_manager.middleware_data.get("repo")
    search_query = dialog_manager.dialog_data.get("search_query")

    if search_query:
        subscriptions = await repo.search_subscribes_by_tags(search_query)
    else:
        subscriptions = await repo.get_subscriptions_list()

    return {
        "subscriptions": subscriptions or None,
    }
