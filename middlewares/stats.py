from vkbottle.dispatch.middlewares import BaseMiddleware
from abc import ABC
from vkbottle.bot import Message
from db.main_database import main_db


class StatsMessagesMiddleware(BaseMiddleware[Message], ABC):
    async def post(self) -> None:
        await main_db.add_income(self.event.peer_id)
