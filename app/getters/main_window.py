from datetime import datetime

from aiogram_dialog import DialogManager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

from app.services.repository import Repo


async def main_window_getter(dialog_manager: DialogManager, **kwargs):
    repo: Repo = dialog_manager.middleware_data.get("repo")
    dialog_manager.dialog_data["repo"] = repo
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get("scheduler")
    subs = await repo.get_subscriptions_list()
    current_time = datetime.now(timezone("Europe/Moscow"))
    next_run_time = scheduler.get_jobs()[0].next_run_time
    minutes_until_next_run = int((next_run_time - current_time).total_seconds() / 60)

    return {
        "minutes_until_next_update": f"{str(minutes_until_next_run)}",
        "subs_counter": f"{str(len(subs))}",
    }
