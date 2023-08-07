from vkbottle.dispatch.middlewares import BaseMiddleware
from vkbottle.bot import Message
from abc import ABC
from db_api.db_engine import db
from loader import bot


class KombuchaMiddleware(BaseMiddleware[Message], ABC):
    async def post(self) -> None:
        if self.event.peer_id > 2000000000 and self.event.from_id > 0:
            last_id = await db.select([db.Chat.last_user_id]).where(db.Chat.chat_id == self.event.chat_id).gino.scalar()
            if last_id != self.event.from_id:
                await (db.User.update.values(kombucha=db.User.kombucha + 0.01).
                       where(db.User.user_id == self.event.from_id)).gino.status()
                await db.Chat.update.values(last_user_id=self.event.from_id).where(db.Chat.chat_id ==
                                                                                   self.event.chat_id).gino.status()


bot.labeler.message_view.register_middleware(KombuchaMiddleware)
