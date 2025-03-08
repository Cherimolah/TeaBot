from abc import ABC
from typing import List, Union, Tuple, Dict
import time

from vkbottle.bot import Message, MessageEvent
from vkbottle.dispatch.rules.base import ABCRule
from sqlalchemy import and_
from vkbottle_types.objects import MessagesMessageActionStatus

from config import PREFIXES, rangnames, ADMIN_ID, GROUP_ID
from utils.parsing_users import get_id_mention_from_message
from utils.parsing import parse_period
from db_api.db_engine import db
from loader import bot


ai_users = set()


class InteractionUsers(ABCRule, ABC):
    def __init__(self, command: str, check_chat: bool = True, self_protect: bool = True, return_himself=False,
                 offset: int = 0):
        self.command = command
        self.check_chat = check_chat
        self.self_protect = self_protect
        self.return_himself = return_himself
        self.offset = offset

    async def check(self, m: Message):
        for prefix in PREFIXES:
            string = " ".join(m.text.split(" ")[:self.offset + 1]).lower()
            if string == self.command or string == prefix + self.command:
                to_user_id = await get_id_mention_from_message(m, self.check_chat, self.self_protect,
                                                               self.return_himself)
                if not to_user_id:
                    return False
                return {"to_user_id": to_user_id}
        return False


class ChangeSettingsChat(ABCRule, ABC):
    async def check(self, m: Message):
        if m.peer_id < 2000000000:
            return False
        rang, admin = await db.select([db.UserToChat.rang, db.UserToChat.admin]).where(
            and_(db.UserToChat.user_id == m.from_id, db.UserToChat.chat_id == m.chat_id)).gino.first()
        if rang < 3 and admin < 1:
            await m.reply(f"❗ Менять настройки беседы могут только обладатели ранга {rangnames[3]} и выше или "
                          "администраторы")
            return False
        return True


class AdminCommand(ABCRule, ABC):
    def __init__(self, command: str, min_rang: int, need_time: bool = False, check_chat=True, for_all=False):
        self.command = command
        self.min_rang = min_rang
        self.need_time = need_time
        self.check_chat = check_chat
        self.for_all = for_all

    async def check(self, m: Message):
        space = self.command.count(' ')
        args = m.text.lower().split()
        command_words = args[:space + 1]
        command = " ".join(command_words)
        for prefix in PREFIXES:
            if command == self.command or command == prefix + self.command:
                if not self.for_all:
                    to_user_id = await get_id_mention_from_message(m, check_chat=self.check_chat)
                else:
                    to_user_id = None
                if not to_user_id and not self.for_all:
                    return False
                if not self.for_all and to_user_id:
                    exist = await db.select([db.UserToChat.user_id]).where(
                        and_(db.UserToChat.user_id == to_user_id, db.UserToChat.chat_id == m.chat_id)).gino.scalar()
                    if not exist:
                        await m.reply('🤷‍♂ Указанный пользователь не зарегистрирован в этом чате')
                        return False
                if m.from_id < 0:
                    is_group_chat = await db.Chat.select('is_group').where(db.Chat.chat_id == m.from_id).gino.scalar()
                    members = await bot.api.messages.get_conversation_members(m.peer_id)
                    return is_group_chat and m.from_id == members.items[0].member_id
                from_user_rang, from_user_admin = await (db.UserToChat.select('rang', 'admin')
                                                         .where(and_(db.UserToChat.user_id == m.from_id,
                                                                     db.UserToChat.chat_id == m.chat_id))
                                                         ).gino.first()
                if from_user_rang < self.min_rang and from_user_admin < 1:
                    await m.reply(f"🙅‍♂ Команда доступна только с ранга {rangnames[self.min_rang]}")
                    return False
                if self.for_all:
                    return True
                can_increase = await db.is_higher(m.chat_id, m.from_id, to_user_id)
                if not can_increase:
                    await m.reply("🙅‍♂ Пользователь выше или одинакового с вами ранга")
                    return False
                if self.need_time:
                    to_time = parse_period(m)
                    if to_time == -1 or to_time - time.time() > 3153600000:  # 100 years
                        await m.reply("🤷‍♂ Неверный период")
                        return False
                    return {"to_user_id": to_user_id, "to_time": to_time}
                return {"to_user_id": to_user_id}
        return False


class Command(ABCRule, ABC):
    def __init__(self, commands: Union[List[str], str], returning_args: bool = True, args_names: Tuple[str, ...] = None,
                 null_args: bool = True):
        if isinstance(commands, str):
            commands = [commands]
        patterns = [f"{prefix}{comm}" for comm in commands for prefix in PREFIXES]
        self.patterns = patterns
        self.returning_args = returning_args
        self.args_names = args_names
        self.null_args = null_args

    async def check(self, event: Message):
        for pattern in self.patterns:
            if self.null_args and event.text.lower() == pattern:
                return True
            if not self.null_args and event.text.lower().startswith(pattern):
                if not self.returning_args:
                    return True
                values = event.text.lower()[len(pattern):].lstrip().split(" ")
                if len(values) != len(self.args_names):
                    return False
                return {name: values[i] for i, name in enumerate(self.args_names)}
        return False


class CommandWithAnyArgs(ABCRule, ABC):
    def __init__(self, command: str, need_values: bool = False, name_args: str = None):
        self.command = command
        self.need_values = need_values
        self.name_args = name_args

    async def check(self, event: Message):
        for prefix in PREFIXES:
            if event.text.lower().startswith(prefix + self.command):
                if self.need_values:
                    values = " ".join(event.text.split(" ")[1 + len(prefix.split(" ")) - 1:])
                    return {self.name_args or "values": values}
                return True
        return False


class AdminPanelCommand(ABCRule, ABC):
    def __init__(self, command: str):
        self.command = command

    async def check(self, m: Message):
        return m.from_id == ADMIN_ID and m.text.lower().startswith(self.command)


invites = [
    MessagesMessageActionStatus.CHAT_INVITE_USER_BY_MESSAGE_REQUEST,
    MessagesMessageActionStatus.CHAT_INVITE_USER,
    MessagesMessageActionStatus.CHAT_INVITE_USER_BY_LINK
]


class GroupInvited(ABCRule, ABC):
    async def check(self, m: Message):
        return m.action is not None and m.action.type in invites and m.action.member_id and m.action.member_id == -GROUP_ID


class UserInvited(ABCRule, ABC):
    async def check(self, m: Message) -> Union[bool, Dict[str, List[int]]]:
        if m.action and m.action.type in invites:
            if m.action.member_id and m.action.member_id > 0:
                return {"users_invited": [m.action.member_id]}
            else:
                user_ids_reg = {x[0] for x in await db.select([db.UserToChat.user_id]).where(
                    db.UserToChat.chat_id == m.chat_id).gino.all()}
                user_ids = {x.member_id for x in (await bot.api.messages.get_conversation_members(m.peer_id)).items if
                            x.member_id > 0}
                users_not_found = list(user_ids - user_ids_reg)
                return {"users_invited": users_not_found}
        return False


class UserKicked(ABCRule, ABC):
    async def check(self, m: Message):
        return m.action is not None and m.action.type == MessagesMessageActionStatus.CHAT_KICK_USER and \
            0 < m.action.member_id != m.from_id


class UserLeft(ABCRule, ABC):
    async def check(self, m: Message):
        return m.action is not None and m.action.type == MessagesMessageActionStatus.CHAT_KICK_USER and \
            0 < int(m.action.member_id) == m.from_id


class RPCommandRule(ABCRule, ABC):
    def __init__(self, command: str):
        self.patterns = [f"{x}{command}" for x in PREFIXES]
        self.command = command

    async def check(self, event: Message):
        msg_text = event.text.lower().replace("\n", " ")
        for pattern in self.patterns:
            if msg_text.startswith(pattern):
                return {"command": self.command}
        return False


class OwnerRPCommand(ABCRule, ABC):
    def __init__(self, owner: int = None):
        self.owner = owner

    async def check(self, event: Message):
        if not self.owner or self.owner == event.from_id:
            return {"owner": self.owner}


class GameExists(ABCRule, ABC):
    async def check(self, m: Message):
        if m.payload and m.payload.get("game_id"):
            game = await db.RouletteGame.get(m.payload["game_id"])
            if game:
                return {"game": game}
            else:
                await m.answer("Игры нет такой! Не ломай бота")
                return False
        return False


class BotMentioned(ABCRule, ABC):
    async def check(self, m: Message):
        if m.text.startswith(f'[club{GROUP_ID}|') or (m.reply_message and m.reply_message.from_id == -GROUP_ID) or (m.fwd_messages and m.fwd_messages[0].from_id == -GROUP_ID):
            return True


class AIFree(ABCRule, ABC):
    async def check(self, m: Message):
        if m.from_id in ai_users:
            await m.reply('🙅‍♂️ Ожидайте ответа')
            return False
        ai_users.add(m.from_id)
        return True


class AIMode(ABCRule, ABC):
    async def check(self, m: Message):
        glue_mode = await db.select([db.User.glue_mode]).where(db.User.user_id == m.from_id).gino.scalar()
        if not glue_mode:
            return True
        return False


class GlueMode(ABCRule, ABC):
    async def check(self, m: Message):
        glue_mode = await db.select([db.User.glue_mode]).where(db.User.user_id == m.from_id).gino.scalar()
        return glue_mode


class NoAttachment(ABCRule, ABC):
    async def check(self, m: Message):
        return False if m.attachments else True
