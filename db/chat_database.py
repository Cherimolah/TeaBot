import aiosqlite3
from vkbottle_types.responses.messages import MessagesGetConversationMembers
from utils.vkscripts import get_cases_users


class ChatDB:
    async def connect(self, chat_id):
        self.db: aiosqlite3.Connection = await aiosqlite3.connect(f"chats/{chat_id}.db")
        self.sql: aiosqlite3.Cursor = await self.db.cursor()
        self.chat_id = chat_id
        self.peer_id = chat_id + 2e9
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

        self.db: aiosqlite3.Connection = await aiosqlite3.connect(f"chats/{chat_id}.db")
        self.sql: aiosqlite3.Cursor = await self.db.cursor()
        self.chat_id = chat_id
        self.peer_id = chat_id + 2e9

        await self.sql.execute("CREATE TABLE IF NOT EXISTS users (id INT, name TEXT, surname TEXT, from_name TEXT,"
                               " from_surname TEXT, to_name TEXT, to_surname TEXT, naming TEXT, surnaming TEXT,"
                               " by_name TEXT DEFAULT NULL, by_surname TEXT, about_name TEXT, about_surname TEXT,"
                               " nickname TEXT, sex BIGINT, screen_name TEXT, rang INT, admin INT,"
                               " mute_time INT DEFAULT -1, ban_time INT DEFAULT -1, kombucha REAL DEFAULT 0.0,"
                               " kombucha_time BIGINT DEFAULT 0, join_date INTEGER, invited_by INTEGER,"
                               " UNIQUE ('id') ON CONFLICT IGNORE)")
        await self.sql.execute("CREATE TABLE IF NOT EXISTS groups (id INT, name TEXT, screen_name TEXT, admin INT, "
                               "ban_time INT, join_date INT, invited_by INT, UNIQUE ('id') ON CONFLICT IGNORE)")
        await self.sql.execute("CREATE TABLE IF NOT EXISTS warns (user_id INT UNIQUE, from_user_id INT, to_time INT)")

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

