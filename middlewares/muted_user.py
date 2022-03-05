from vkbottle.dispatch.middlewares import BaseMiddleware
from abc import ABC
from vkbottle.bot import Message
from middlewares.registration import registered_chats
import time


class MutedUserMiddleware(BaseMiddleware[Message], ABC):

    async def pre(self) -> None:
        if self.event.chat_id in registered_chats and self.event.from_id > 0:
            chat_db = registered_chats[self.event.chat_id]
            await chat_db.sql.execute("SELECT mute_time FROM users WHERE id = ?", (self.event.from_id,))
            mute_time = (await chat_db.sql.fetchone())[0]
            if mute_time == 0 or mute_time > time.time():
                await chat_db.set_warn(self.event.from_id, 0, int(time.time()+2592000), self.event)
                self.stop()
