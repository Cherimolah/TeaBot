from abc import ABC
from typing import List, Union, Tuple
import time

from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import ABCRule
from sqlalchemy import and_
from vkbottle_types.objects import MessagesMessageActionStatus

from config import PREFIXES, rangnames, ADMIN_ID, GROUP_ID
from utils.parsing_users import get_id_mention_from_message
from utils.parsing import parse_period
from db_api.db_engine import db
from loader import bot


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
            string = " ".join(m.text.split(" ")[:self.offset+1]).lower()
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
            await bot.reply_msg(m, f"❗ Менять настройки беседы могут только обладатели ранга {rangnames[3]} и выше или "
                                  "администраторы")
            return False
        return True


class AdminCommand(ABCRule, ABC):
    def __init__(self, command: str, min_rang: int, need_time: bool = False, check_chat = False):
        self.command = command
        self.min_rang = min_rang
        self.need_time = need_time
        self.check_chat = check_chat

    async def check(self, m: Message):
        for prefix in PREFIXES:
            if m.text.split(" ")[0].lower() == self.command or m.text.split(" ")[0].lower() == prefix + self.command:
                to_user_id = await get_id_mention_from_message(m, check_chat=False)
                if not to_user_id:
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
                    await bot.reply_msg(m, f"🙅‍♂ Команда доступна только с ранга {rangnames[self.min_rang]}")
                    return False
                can_increase = await db.is_higher(m.chat_id, m.from_id, to_user_id)
                if not can_increase:
                    await bot.reply_msg(m, "🙅‍♂ Пользователь выше или одинакового с вами ранга")
                    return False
                if self.need_time:
                    to_time = parse_period(m)
                    if to_time == -1 or to_time - time.time() > 3153600000:  # 100 years
                        await bot.reply_msg(m, "🤷‍♂ Неверный период")
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
                    values = " ".join(event.text.split(" ")[1+len(prefix.split(" "))-1:])
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
        return m.action is not None and m.action.type in invites and m.action.member_id == -GROUP_ID


class UserInvited(ABCRule, ABC):
    async def check(self, m: Message):
        return m.action is not None and m.action.type in invites and m.action.member_id > 0


class UserKicked(ABCRule, ABC):
    async def check(self, m: Message):
        return m.action is not None and m.action.type == MessagesMessageActionStatus.CHAT_KICK_USER and \
               0 < m.action.member_id != m.from_id


class UserLeft(ABCRule, ABC):
    async def check(self, m: Message):
        return m.action is not None and m.action.type == MessagesMessageActionStatus.CHAT_KICK_USER and \
               0 < m.action.member_id == m.from_id


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


