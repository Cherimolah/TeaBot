from vkbottle.dispatch.middlewares import BaseMiddleware
from abc import ABC
from vkbottle.bot import Message
import time
from db_api.db_engine import db
from utils.views import set_warn
from utils.parsing import parse_unix_to_date
from sqlalchemy import and_
from loader import bot


class MutedUserMiddleware(BaseMiddleware[Message], ABC):

    async def pre(self) -> None:
        if self.event.from_id > 0 and self.event.peer_id > 2000000000 and await db.User.get(self.event.from_id):
            mute = await (db.select([db.User.user_id, db.User.names[2], db.User.nickname, db.Punishment.closing_at])
                          .select_from(db.User.join(db.Punishment, db.Punishment.from_user_id == db.User.user_id))
                          .where(and_(db.Punishment.type == 1, db.Punishment.to_user_id == self.event.from_id,
                                      db.Punishment.chat_id == self.event.chat_id))).gino.first()
            if mute is not None:
                from_user_id, from_user_name, from_user_nickname, mute_closing_at = mute
                await bot.reply_msg(
                    self.event,
                    f"🤐 {await db.get_mention_user(self.event.from_id, 1)} у вас мут "
                    f"{parse_unix_to_date(mute_closing_at)} "
                    f"от [id{from_user_id}|{from_user_name if from_user_nickname is None else from_user_nickname}]")
                await set_warn(self.event.chat_id, from_user_id, self.event.from_id, int(time.time() + 259200))
                self.stop()


bot.labeler.message_view.register_middleware(MutedUserMiddleware)
