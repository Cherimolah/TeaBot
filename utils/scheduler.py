from abc import ABC, abstractmethod
from typing import Optional, List, Callable
import datetime
import asyncio


class BaseTypeScheduler(ABC):

    @abstractmethod
    def count_delta(self) -> int:
        pass


class Cron(BaseTypeScheduler, ABC):
    def __init__(self, hour: Optional[int] = 0, minute: Optional[int] = 0, second: Optional[int] = 0):
        self.hour = hour
        self.minute = minute
        self.second = second
        self._triggered = False

    def count_delta(self) -> int:
        now = datetime.datetime.now()
        date = datetime.datetime(now.year, now.month, now.day, self.hour, self.minute, self.second)
        if self._triggered:
            self._triggered = False
            return (now - (date + datetime.timedelta(days=1))).seconds
        if now > date:
            date = date + datetime.timedelta(days=1)
        self._triggered = True
        return (date - now).seconds


class Interval(BaseTypeScheduler, ABC):

    def __init__(self, years: Optional[int] = 0, months: Optional[int] = 0, days: Optional[int] = 0,
                 hours: Optional[int] = 0, minutes: Optional[int] = 0, seconds: Optional[int] = 0):
        self.years = years
        self.months = months
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def count_delta(self) -> int:
        seconds = self.years * 31536000
        seconds += self.months * 108000
        seconds += self.days * 86400
        seconds += self.hours * 3600
        seconds += self.minutes * 60
        seconds += self.seconds
        return seconds


class Task:

    def __init__(self, type_: BaseTypeScheduler, func: Callable, next_run_time: Optional[datetime.datetime] = None):
        self.type = type_
        self.next_run_time = next_run_time
        self.func = func


class AsyncIOScheduler:

    def __init__(self):
        self.tasks: List[Callable] = []

    def add_task(self, type_: BaseTypeScheduler, next_run_time: Optional[datetime.datetime] = None):

        def wrapper(func: Callable):

            async def decorator(*args, **kwargs):
                if next_run_time:
                    now = datetime.datetime.now()
                    delta = next_run_time.timestamp() - now.timestamp()
                    await asyncio.sleep(delta)
                    await func(*args, **kwargs)
                while True:
                    await asyncio.sleep(type_.count_delta())
                    await func(*args, *kwargs)

            self.tasks.append(decorator)

            return decorator

        return wrapper

    def start(self):
        loop = asyncio.get_event_loop()
        for task in self.tasks:
            loop.create_task(task())

