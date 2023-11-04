from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone


class Schedules:
    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler

    async def get_next_update(self) -> int:
        """return minutes before next run"""
        current_time = datetime.now(timezone("Europe/Moscow"))
        next_run_time = self.scheduler.get_jobs()[0].next_run_time
        return int((next_run_time - current_time).total_seconds() / 60)

    async def set_update_interval(self, hours: int) -> bool:
        pass
