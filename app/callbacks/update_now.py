from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram.types import CallbackQuery
from app.services.schedules import Schedules


async def on_update_now(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    scheduler: Schedules = manager.middleware_data.get("scheduler")
    await callback.answer("Запущена проверка обновлений!")
    await scheduler.do_next_job_now()
