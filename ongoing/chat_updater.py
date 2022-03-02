from middlewares.registration import registered_chats
from typing import NoReturn
from utils.vkscripts import get_conversations_members, get_cases_users
from blueprints.blueprint import bp


async def update_chats() -> NoReturn:
    while True:

        # Получение списка ответов от вк актульной информации об участниках беседы
        peer_ids = [int(x + 2e9) for x in registered_chats.keys()]
        chats = [y for x in [await get_conversations_members(peer_ids[i:min(len(peer_ids), i + 25)]) \
                             for i in range(0, len(peer_ids), 25)] for y in x]

        # Обновление каждого чата
        for i in range(len(chats)):

            # Пропуск незарегистрированных бесед и бесед без доступа к участникам
            chat_db = registered_chats[int(peer_ids[i] - 2e9)]
            if not chats[i] or chat_db is None:
                continue

            await chat_db.sql.execute("UPDATE users SET ban_time = -4 WHERE ban_time = -1")  # Флаг обновление статуса

            # Получение списка имён пользователей из беседы отсортрованных по падежам
            users_ids = [{"id": x['member_id'], "admin": 2 if "is_owner" in x else 1 if "is_admin" in x else 0} for x in
                         chats[i]['items'] if x['member_id'] > 0]
            users_cases = [await get_cases_users([x['id'] for x in users_ids][i1:i1 + 999]) for i1 in
                           range(0, len(users_ids), 999)]
            cases = [[y for x in users_cases for y in x[i1]] for i1 in range(6)]

            # Внесение данных о каждом пользователе
            for i1 in range(len(users_ids)):

                if "screen_name" in cases[0][i1]:
                    screen_name = cases[0][i1]['screen_name']
                else:
                    screen_name = f"id{users_ids[i1]['id']}"

                # Отправка сообщения об изменении состояния участника в чайной беседе
                if peer_ids[i] == 2000000009:
                    await chat_db.sql.execute("SELECT id FROM users")
                    res = await chat_db.sql.fetchall()
                    ids = [x[0] for x in res]
                    if users_ids[i1]['id'] not in ids:
                        await bp.write_msg(2000000009,
                                           f"✋ Приветсвую тебя, чаеман [id{users_ids[i1]['id']}|{cases[0][i1]['first_name']} {cases[0][i1]['last_name']}]")

                    await chat_db.sql.execute("SELECT id FROM users WHERE ban_time = ?", (-2,))
                    res = await chat_db.sql.fetchall()
                    ids = [x[0] for x in res]
                    if users_ids[i1]['id'] in ids:
                        await bp.write_msg(2000000009,
                                           f"✋ [id{users_ids[i1]['id']}|{cases[0][i1]['first_name']} {cases[0][i1]['last_name']}] вернул{'ась' if cases[0][i1]['sex'] == 1 else 'ся'} в беседу")

                    await chat_db.sql.execute("SELECT id, name, surname, sex FROM users WHERE ban_time = -5")
                    res = await chat_db.sql.fetchall()
                    for user in res:
                        await bp.write_msg(2000000009,
                                           f"😢 [id{user[0]}|{user[1]} {user[2]}] покинул{'а' if user[3] == 1 else ''} беседу")
                        await chat_db.sql.execute("UPDATE users SET ban_time = ? WHERE id = ?", (-2, user[0]))

                # Внесение и обновление данных о пользователе
                await chat_db.sql.execute("INSERT INTO users (id, name, surname, from_name, from_surname, to_name, "
                                          "to_surname, naming, surnaming, by_name, by_surname, about_name, about_surname, "
                                          "sex, screen_name, rang, admin, join_date, invited_by, ban_time) VALUES (?, ?, ?, ?, ?, ?, ?, "
                                          "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                          (users_ids[i1]['id'], cases[0][i1]['first_name'], cases[0][i1]['last_name'],
                                           cases[1][i1]['first_name'], cases[1][i1]['last_name'],
                                           cases[2][i1]['first_name'], cases[2][i1]['last_name'],
                                           cases[3][i1]['first_name'], cases[3][i1]['last_name'],
                                           cases[4][i1]['first_name'], cases[4][i1]['last_name'],
                                           cases[5][i1]['first_name'], cases[5][i1]['last_name'],
                                           cases[0][i1]['sex'], screen_name,
                                           5 if users_ids[i1]['admin'] == 2 else 4 if users_ids[i1][
                                                                                          'admin'] == 1 else 0,
                                           users_ids[i1]['admin'],
                                           chats[i]['items'][i1]['join_date'], chats[i]['items'][i1]['invited_by'], -1))
                await chat_db.sql.execute(
                    "UPDATE users SET name = ?, surname = ?, from_name = ?, from_surname = ?, to_name = ?, "
                    "to_surname = ?, naming = ?, surnaming = ?, by_name = ?, by_surname = ?, about_name = ?, "
                    "about_surname = ?, sex = ?, screen_name = ?, admin = ?, join_date = ?, "
                    "invited_by = ?, ban_time = ? WHERE id = ?", (cases[0][i1]['first_name'], cases[0][i1]['last_name'],
                                                                  cases[1][i1]['first_name'], cases[1][i1]['last_name'],
                                                                  cases[2][i1]['first_name'], cases[2][i1]['last_name'],
                                                                  cases[3][i1]['first_name'], cases[3][i1]['last_name'],
                                                                  cases[4][i1]['first_name'], cases[4][i1]['last_name'],
                                                                  cases[5][i1]['first_name'], cases[5][i1]['last_name'],
                                                                  cases[0][i1]['sex'], screen_name,
                                                                  users_ids[i1]['admin'],
                                                                  chats[i]['items'][i1]['join_date'],
                                                                  chats[i]['items'][i1]['invited_by'], -1,
                                                                  users_ids[i1]['id']))

            # Установка флага "вышел или исключён"
            await chat_db.sql.execute("UPDATE users SET ban_time = -5 WHERE ban_time = -4")

            # Список групп
            groups_ids = [{"id": -x['member_id'], "admin": 2 if "is_owner" in x else 1 if "is_admin" in x else 0,
                           "join_date": x['join_date'], "invited_by": x['invited_by']} for x
                          in chats[i]['items'] if x['member_id'] < 0]
            groups_ids.sort(key=lambda x: x['id'])

            await chat_db.sql.execute("UPDATE groups SET ban_time = -4 WHERE ban_time = -1")

            # Обновление данных о группах
            for i1 in range(len(groups_ids)):
                await chat_db.sql.execute("INSERT INTO groups VALUES (?, ?, ?, ?, ?, ?, ?)",
                                          (-groups_ids[i1]['id'], chats[i]['groups'][i1]['name'],
                                           chats[i]['groups'][i1]['screen_name'], groups_ids[i1]['admin'], -1,
                                           groups_ids[i1]['join_date'], groups_ids[i1]['invited_by']))
                await chat_db.sql.execute("UPDATE groups SET name = ?, screen_name = ?, admin = ?, ban_time = ?, "
                                          "join_date = ?, invited_by = ? WHERE id = ?",
                                          (chats[i]['groups'][i1]['name'], chats[i]['groups'][i1]['screen_name'],
                                           groups_ids[i1]['admin'], -1, groups_ids[i1]['join_date'],
                                           groups_ids[i1]['invited_by'], -groups_ids[i1]['id']))

            # Установка флага "кик", т.к. группы самостоятельно не выходят обычно
            await chat_db.sql.execute("UPDATE groups SET ban_time = -2 WHERE ban_time = -4")

            await chat_db.db.commit()
