from blueprints.blueprint import bp
from vkbottle import ABCRule
from abc import ABC
from db.main_database import main_db
import asyncio
from vkbottle.bot import Message
import re
from utils.parsing_users import get_id_mention_from_message
from middlewares.registration import registered_chats


mention_regex = re.compile(r"^\[(?P<type>id|club|public)(?P<id>\d*)\|(?P<text>.+)\] ")
link_regex = re.compile(r"^https:/(?P<type>/|/m.)vk.com/(?P<screen_name>\w*) ")


class RPCommandRule(ABCRule, ABC):
    def __init__(self, command: str):
        self.pattern = re.compile(fr"^{command}")

    async def check(self, event: Message):
        msg_text = event.text.lower().replace("\n", " ")
        return re.search(self.pattern, event.text) is not None


async def add_rp_commands():
    commands = [x[0] for x in await (await main_db.sql.execute("SELECT command FROM rp_commands")).fetchall()]
    for com in commands:
        @bp.on.chat_message(RPCommandRule(com))
        async def role_play_command(m: Message):
            to_user_id = await get_id_mention_from_message(m)
            if to_user_id == 0:
                await bp.reply_msg(m, "🙅 Пользователь не указан")
                return
            if to_user_id == -1:
                await bp.reply_msg(m, "🙅 Пользователь отсутствует в беседе")
                return
            msg_text = m.text.lower().replace("\n", " ")
            rp_command = ""
            for command in commands:
                if msg_text.startswith(command):
                    rp_command = command
                    break
            chat_db = registered_chats[m.chat_id]
            sex = (await (await chat_db.sql.execute("SELECT sex FROM users WHERE id = ?", (m.from_id,))).fetchone())[0]
            if sex == 2:
                await main_db.sql.execute("SELECT emoji, action, specify, name_case FROM rp_commands WHERE command = ?",
                                          (rp_command,))
            else:
                await main_db.sql.execute("SELECT emoji, wom_action, specify, name_case FROM rp_commands WHERE"
                                          " command = ?", (rp_command,))
            emoji, action, specify, name_case = await main_db.sql.fetchone()
            user_name = await chat_db.get_mention_user(m.from_id, 0)
            to_user_name = await chat_db.get_mention_user(to_user_id, name_case)
            replic = m.text.replace("\n", " ")[len(rp_command)+1:].lstrip()
            match = re.search(mention_regex, replic)
            if match is not None:
                replic = replic[match.span()[1]:].lstrip()
            else:
                match = re.search(link_regex, replic)
                if match is not None:
                    replic = replic[match.span()[1]:].lstrip()
            await bp.reply_msg(m, f"{emoji} {user_name} {action} {specify if specify is not None else ''} "
                                  f"{to_user_name}\n"
                                  f"{f'💬С репликой «{replic}»' if replic != '' else ''}")

asyncio.get_event_loop().run_until_complete(add_rp_commands())
