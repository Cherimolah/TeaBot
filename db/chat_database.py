import aiosqlite
from vkbottle_types.responses.messages import MessagesGetConversationMembers
from utils.vkscripts import get_cases_users
from blueprints.blueprint import bp
import time
from utils.parsing import parse_unix_to_date
from vkbottle.bot import Message


class ChatDB:
    async def connect(self, chat_id):
        self.db: aiosqlite.Connection = await aiosqlite.connect(f"chats/{chat_id}.db")
        self.sql: aiosqlite.Cursor = await self.db.cursor()
        self.chat_id = chat_id
        self.peer_id = chat_id + 2000000000
        return self

    async def insert_users(self, members_dict):
        user_ids = [x for x in members_dict.keys() if x > 0]
        user_cases = await get_cases_users(user_ids)

        for i in range(len(user_cases[0])):
            user = members_dict[user_cases[0][i]['id']]

            for i1 in range(6):
                user_cases[i1][i][f"name{i1}"] = user_cases[i1][i]['first_name']
                user_cases[i1][i].pop('first_name')
                user_cases[i1][i][f"surname{i1}"] = user_cases[i1][i]['last_name']
                user_cases[i1][i].pop('last_name')
                user = {**user, **user_cases[i1][i]}

            if "screen_name" in user:
                screen_name = user['screen_name']
            else:
                screen_name = f"id{user['id']}"

            await self.sql.execute("INSERT INTO users (id, name, surname, from_name, from_surname, to_name, "
                                   "to_surname, naming, surnaming, by_name, by_surname, about_name, about_surname, "
                                   "sex, screen_name, rang, admin, join_date, invited_by) VALUES (?, ?, ?, ?, ?, ?, ?, "
                                   "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                   (user['id'], user['name0'], user['surname0'], user['name1'], user['surname1'],
                                    user['name2'], user['surname2'], user['name3'], user['surname3'],
                                    user['name4'], user['surname4'], user['name5'], user['surname5'],
                                    user['sex'], screen_name,
                                    user['rang'], user['admin'], user['join_date'], user['invited_by']))
            members_dict.pop(user['id'])

        await self.db.commit()

    async def insert_groups(self, members_dict, members: MessagesGetConversationMembers):
        for group in members.groups:
            await self.sql.execute("INSERT INTO groups VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (-group.id, group.name, group.screen_name, members_dict[-group.id]['admin'], -1,
                                    members_dict[-group.id]['join_date'], members_dict[-group.id]['invited_by']))
        await self.db.commit()

    async def create(self, chat_id: int, members_response: MessagesGetConversationMembers):
        members = members_response.items

        self.db: aiosqlite.Connection = await aiosqlite.connect(f"chats/{chat_id}.db")
        self.sql: aiosqlite.Cursor = await self.db.cursor()
        self.chat_id = chat_id
        self.peer_id = chat_id + 2000000000

        await self.sql.execute("CREATE TABLE IF NOT EXISTS users (id INT, name TEXT, surname TEXT, from_name TEXT,"
                               " from_surname TEXT, to_name TEXT, to_surname TEXT, naming TEXT, surnaming TEXT,"
                               " by_name TEXT DEFAULT NULL, by_surname TEXT, about_name TEXT, about_surname TEXT,"
                               " nickname TEXT, sex BIGINT, screen_name TEXT, rang INT, admin INT,"
                               " mute_time INT DEFAULT -1, ban_time INT DEFAULT -1, kombucha REAL DEFAULT 0.0,"
                               " kombucha_time BIGINT DEFAULT 0, join_date INTEGER, invited_by INTEGER,"
                               " UNIQUE ('id') ON CONFLICT IGNORE)")
        await self.sql.execute("CREATE TABLE IF NOT EXISTS groups (id INT, name TEXT, screen_name TEXT, admin INT, "
                               "ban_time INT, join_date INT, invited_by INT, UNIQUE ('id') ON CONFLICT IGNORE)")
        await self.sql.execute("CREATE TABLE IF NOT EXISTS warns (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                               "user_id INT, from_user_id INT, to_time INT)")

        users_count = 0
        groups_count = 0
        members_dict = {}

        for member in members:
            members_dict[member.member_id] = {"rang": 5 if member.is_owner else 4 if member.is_admin else 0,
                                              "admin": 2 if member.is_owner else 1 if member.is_admin else 0,
                                              "invited_by": member.invited_by, "join_date": member.join_date}
            if member.member_id > 0:
                users_count += 1
            else:
                groups_count += 1
            if users_count >= 999:
                await self.insert_users(members_dict)

        await self.insert_groups(members_dict, members_response)
        await self.insert_users(members_dict)
        await self.db.commit()
        return self

    async def get_name_user(self, user_id: int, name_case: int) -> str:
        if user_id < 0:
            await self.sql.execute("SELECT name FROM groups WHERE id = ?", (user_id,))
            return (await self.sql.fetchone())[0]
        await self.sql.execute("SELECT nickname FROM users WHERE id = ?", (user_id,))
        nickname = (await self.sql.fetchone())[0]
        if nickname is not None:
            return nickname
        if name_case == 0:
            await self.sql.execute("SELECT name, surname FROM users WHERE id = ?", (user_id,))
        elif name_case == 1:
            await self.sql.execute("SELECT from_name, from_surname FROM users WHERE id = ?", (user_id,))
        elif name_case == 2:
            await self.sql.execute("SELECT to_name, to_surname FROM users WHERE id = ?", (user_id,))
        elif name_case == 3:
            await self.sql.execute("SELECT naming, surnaming FROM users WHERE id = ?", (user_id,))
        elif name_case == 4:
            await self.sql.execute("SELECT by_name, by_surname FROM users WHERE id = ?", (user_id,))
        elif name_case == 5:
            await self.sql.execute("SELECT about_name, about_surname FROM users WHERE id = ?", (user_id,))
        res = await self.sql.fetchone()
        return f"{res[0]} {res[1]}"

    async def get_mention_user(self, user_id: int, name_case: int) -> str:
        name = await self.get_name_user(user_id, name_case)
        return f"[id{user_id}|{name}]"

    async def is_user_in_chat(self, user_id: int) -> bool:
        await self.sql.execute("SELECT ban_time FROM users WHERE id = ?", (user_id,))
        return (await self.sql.fetchone())[0] == -1

    async def is_admin_user(self, user_id: int) -> bool:
        await self.sql.execute("SELECT admin FROM users WHERE id = ?", (user_id,))
        return (await self.sql.fetchone())[0] > 0

    async def set_warn(self, user_id: int, from_user_id: int, to_time: int, m: Message):

        if user_id < 0:
            await bp.reply_msg(m, "🙅 Группам предупреждения не выдаются")
            return

        if not await self.is_user_in_chat(user_id):
            await bp.reply_msg(m, "🙅 Пользователя нет в беседе")
            return

        if from_user_id == 0:
            from_user_name = "автоматическая выдача предупреждений"
        else:
            from_user_name = await self.get_mention_user(from_user_id, 1)

        await self.sql.execute("INSERT INTO warns (user_id, from_user_id, to_time) VALUES (?, ?, ?)",
                               (user_id, from_user_id, to_time))
        user_name = await self.get_mention_user(user_id, 0)
        await self.sql.execute("SELECT COUNT(*) FROM warns WHERE user_id = ?", (user_id,))
        count = (await self.sql.fetchone())[0]
        await bp.reply_msg(m, f"⚠ {user_name}, вам выдано предупрждение до "
                              f"[{parse_unix_to_date(time.time() + 2592000)}] "
                              f"от {from_user_name}\n"
                              f"Всего предупреждений {count}/5", disable_mentions=False)

        if count >= 5:
            if await self.is_admin_user(user_id):
                await bp.reply_msg(m, f"🚫 {user_name}, у вас достигнут лимит предупреждений, но я не могу "
                                      f"вас исключить из-за настроек беседы", disable_mentions=False)
            else:
                await bp.reply_msg(m, f"🚫 {user_name}, вы были исключены из беседы за достижение лимита предупреждений",
                                   disable_mentions=False)
                await bp.api.messages.remove_chat_user(self.chat_id, member_id=user_id)
                await self.sql.execute("DELETE FROM warns WHERE user_id = ?", (user_id,))
        await self.db.commit()

