from abc import ABC
import asyncio

from vkbottle.dispatch.middlewares import BaseMiddleware
from vkbottle.bot import Message
from sqlalchemy import and_

from loader import bot, captcha_users
from db_api.db_engine import db


async def delay_delete_message(peer_id: int, cmid: int, time: int = 5):
    await asyncio.sleep(time)
    await bot.api.messages.delete(peer_id=peer_id, cmids=[cmid], delete_for_all=True)


class CaptchaUsers(BaseMiddleware[Message], ABC):

    async def pre(self) -> None:
        m: Message = self.event
        chat_registered = await db.select([db.Chat.chat_id]).where(db.Chat.chat_id == m.chat_id).gino.scalar()
        if m.peer_id > 2000000000 and chat_registered:
            registered = await db.select([db.UserToChat.user_id]).where(
                and_(db.UserToChat.user_id == m.from_id, db.UserToChat.chat_id == m.chat_id)
            ).gino.scalar()
            if m.from_id not in captcha_users and not registered and m.from_id > 0:
                await bot.api.messages.delete(peer_id=m.peer_id, cmids=[m.conversation_message_id], delete_for_all=True)
                self.stop()
            elif m.from_id in captcha_users:
                try:
                    answer = int(m.text)
                except ValueError:
                    await bot.api.messages.delete(peer_id=m.peer_id, cmids=[m.conversation_message_id], delete_for_all=True)
                    self.stop()
                if answer == captcha_users[m.from_id]:
                    message = (await bot.api.messages.send(peer_id=m.peer_id, message='Ответ правильный!'))[0]
                    asyncio.get_event_loop().create_task(
                        delay_delete_message(message.peer_id, message.conversation_message_id)
                    )
                    asyncio.get_event_loop().create_task(
                        delay_delete_message(m.peer_id, m.conversation_message_id)
                    )
                    del captcha_users[m.from_id]
                else:
                    await bot.api.messages.delete(peer_id=m.peer_id, cmids=[m.conversation_message_id],
                                                  delete_for_all=True)
                    self.stop()


bot.labeler.message_view.register_middleware(CaptchaUsers)
