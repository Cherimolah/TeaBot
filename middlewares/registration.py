from vkbottle.dispatch.middlewares import BaseMiddleware
from abc import ABC
from vkbottle.bot import Message
from db.main_database import chat_ids, main_db
from vkbottle import VKAPIError
from blueprints.blueprint import bp
from db.chat_database import ChatDB
import asyncio

registered_chats = {}
for chat in chat_ids:
    registered_chats[chat[0]] = asyncio.get_event_loop().run_until_complete(ChatDB().connect(chat[0]))


class RegistrationMiddleware(BaseMiddleware[Message], ABC):
    async def pre(self) -> None:
        if self.event.peer_id > 2e9 and self.event.chat_id not in registered_chats:
            m = self.event
            try:
                registered_chats[m.chat_id] = None
                members = await bp.api.messages.get_conversation_members(m.peer_id)
                chat_db = await ChatDB().create(m.chat_id, members)
                registered_chats[m.chat_id] = chat_db

                await main_db.sql.execute("INSERT INTO chats VALUES (?, ?, ?)", (m.chat_id, None, None))
                await main_db.db.commit()
                await bp.reply_msg(m, f"✅ Беседа успешно зарегестрирована! Идентификатор беседы: {m.chat_id}")

                await bp.write_msg(671385770, f"Новая беседа! Айди {m.chat_id}\n"
                                              f"Админ: https://vk.com/id{members.items[0].member_id}")
            except VKAPIError:
                registered_chats.pop(m.chat_id)
                await bp.reply_msg(m, "🔒 Выдайте мне права администратора, чтобы пользоваться мной")
