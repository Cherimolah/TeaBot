import traceback

from vkbottle.dispatch.middlewares import BaseMiddleware
from abc import ABC
from vkbottle.bot import Message
from db_api.db_engine import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from config import ADMIN_ID, MY_PEERS
from loader import bot


class StatsMessagesMiddleware(BaseMiddleware[Message], ABC):
    async def post(self):
        if self.event.peer_id < 2000000000:
            await bot.write_msg(ADMIN_ID, f"{await db.get_mention_user(self.event.from_id, 0)} написал"
                                             f"{'a' if await db.is_woman_user(self.event.from_id) else ''}: {self.event.text}")
        if self.event.peer_id not in MY_PEERS:
            await (insert(db.StatsTotal).values(date=datetime.now().date(), income_msgs=1)
                   .on_conflict_do_update(index_elements=[db.StatsTotal.date],
                                          set_=dict(income_msgs=db.StatsTotal.income_msgs+1))).gino.status()


bot.labeler.message_view.register_middleware(StatsMessagesMiddleware)
