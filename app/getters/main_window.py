from aiogram_dialog import DialogManager

from app.services.repository import Repo
from app.services.schedules import Schedules


async def main_window_getter(dialog_manager: DialogManager, **kwargs):
    repo: Repo = dialog_manager.middleware_data.get("repo")
    scheduler: Schedules = dialog_manager.middleware_data.get("scheduler")
    subscribes = await repo.get_subscriptions_list()
    minutes_until_next_run = await scheduler.get_next_update()
    return {
        "minutes_until_next_update": f"{str(minutes_until_next_run)}",
        "subs_counter": f"{str(len(subscribes))}",
    }
