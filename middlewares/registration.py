import traceback

from vkbottle.dispatch.middlewares import BaseMiddleware
from abc import ABC
from vkbottle.bot import Message
from db_api.db_engine import db
from vkbottle import VKAPIError
from asyncpg.exceptions import UniqueViolationError

from loader import bot
from config import ADMIN_ID
from utils.vkscripts import get_cases_users
from utils.parsing import collect_names, convert_date
from utils.parsing_users import parse_user_cases


class RegistrationMiddleware(BaseMiddleware[Message], ABC):
    async def pre(self) -> None:
        if self.event.peer_id > 2000000000 and self.event.from_id == ADMIN_ID and self.event.text == "/айди":
            await self.event.reply(f"Пир: {self.event.peer_id}")
        if self.event.peer_id > 2e9 and not await db.is_chat_registered(
                self.event.chat_id) and self.event.action is None:
            m: Message = self.event
            try:
                members = await bot.api.messages.get_conversation_members(m.peer_id)
                users_ids = [x.member_id for x in members.items if x.member_id > 0]
                users_responses = await parse_user_cases(users_ids)
                await db.register_chat(m.chat_id, members.items, users_responses)
                await m.reply(f"✅ Беседа успешно зарегестрирована! Идентификатор беседы: {m.chat_id}")
                reply = f"Новая беседа! Айди {m.chat_id}\n" \
                        f"Первый в списке: https://vk.com/id{members.items[0].member_id}"
                for member in members.items:
                    if member.is_owner:
                        admin_id = member.member_id
                        reply += f"\nСоздатель: https://vk.com/{'club' if admin_id < 0 else 'id'}{admin_id}"
                        break
                for member in members.items:
                    if member.member_id < 0:
                        continue
                    if member.is_admin:
                        reply += f"\nПервый админ: https://vk.com/id{member.member_id}"
                        break
                try:
                    link = (await bot.api.messages.get_invite_link(self.event.peer_id)).link
                except VKAPIError:
                    link = "Ссылка скрыта настройками приватности"
                reply += f"\nСсылка на конфу: {link}"
                await bot.api.messages.send(ADMIN_ID, reply)
            except VKAPIError:
                await m.reply("🔒 Выдайте мне права администратора, чтобы пользоваться мной\n\n"
                              "Одного доступа к переписке не достаточно")
                await db.Chat.delete.where(db.Chat.chat_id == self.event.chat_id).gino.status()
                self.stop()
            except Exception:
                await db.Chat.delete.where(db.Chat.chat_id == self.event.chat_id).gino.status()
                self.stop()
        if self.event.from_id > 0 and not await db.User.get(self.event.from_id):
            user = (await get_cases_users([self.event.from_id]))[0]
            try:
                await db.User.create(user_id=user.id, names=collect_names(user), sex=user.sex,
                                     screen_name=user.screen_name or f"id{user.id}", birthday=convert_date(user.bdate))
            except UniqueViolationError:
                pass
        if self.event.action and int(self.event.action.member_id) > 0 and not await db.User.get(self.event.action.member_id):
            user = (await get_cases_users([self.event.action.member_id]))[0]
            try:
                await db.User.create(user_id=user.id, names=collect_names(user), sex=user.sex,
                                     screen_name=user.screen_name or f"id{user.id}", birthday=convert_date(user.bdate))
            except UniqueViolationError:
                pass


bot.labeler.message_view.register_middleware(RegistrationMiddleware)
