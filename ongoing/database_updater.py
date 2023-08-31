import datetime
from typing import NoReturn, List, Tuple
from utils.vkscripts import get_conversations_members
from utils.views import send_goodbye, send_hello
from db_api.db_engine import db
import asyncio
from utils.parsing import collect_names, convert_date
from utils.parsing_users import parse_user_cases
from sqlalchemy import and_, not_, update, bindparam
from sqlalchemy.dialects.postgresql import insert
from utils.views import get_names_user, waiting_punishment


async def update_users() -> NoReturn:
    """Обновляет имена пользователей, пол и короткое имя"""
    while True:
        user_ids = [x[0] for x in await db.select([db.User.user_id]).gino.all()]
        users_data = await parse_user_cases(user_ids)
        udata = [dict(names=collect_names(udata), sex=udata.sex,
                      screen_name=udata.screen_name or f"id{udata.id}",
                      birthday=convert_date(udata.bdate), user_id=udata.id) for udata in users_data]
        stmt = update(db.User).where(db.User.user_id == bindparam('user_id')).values({
            "names": bindparam('names'),
            "sex": bindparam("sex"),
            "screen_name": bindparam('screen_name'),
            "birthday": bindparam('birthday'),
            "user_id": bindparam('user_id')
        })
        await db.all(stmt, udata)


async def update_users_in_chats() -> NoReturn:
    """Обновляет информацию о уровнях админки пользователей и состоянии в беседе"""
    while True:
        peer_ids = [x[0] + 2000000000 for x in await db.select([db.Chat.chat_id]).gino.all()]
        for i in range(0, len(peer_ids), 25):
            responses = await get_conversations_members(peer_ids[i:i + 25])
            for index, response in enumerate(responses):
                response, peer_id = response
                if not response:
                    continue
                chat_id = peer_id - 2000000000
                members_ids = {x['member_id'] for x in response['items'] if x["member_id"] > 0}
                users_in_db = {x[0] for x in await db.select([db.UserToChat.user_id]).where(
                    and_(db.UserToChat.chat_id == chat_id, db.UserToChat.in_chat.is_(True))
                ).gino.all()}
                users_found = list(members_ids - users_in_db)
                users_lost = list(users_in_db - members_ids)
                if users_found:
                    user_cases = await parse_user_cases(users_found)
                    users_data = [{"names": get_names_user(i1, user_cases), "sex": bool(user_cases[i1].sex),
                                   "screen_name": user_cases[i1].screen_name if user_cases[
                                       i1].screen_name else f"id{users_found[i1]}",
                                   "user_id": users_found[i1]} for i1 in range(len(users_found))
                                  ]
                    await insert(db.User).values(users_data).on_conflict_do_nothing().gino.scalar()
                is_group = await db.select([db.Chat.is_group]).where(db.Chat.chat_id == chat_id).gino.scalar()
                for user_id in users_lost:
                    await db.UserToChat.update.values(in_chat=False).where(
                        and_(db.UserToChat.user_id == user_id, db.UserToChat.chat_id == chat_id)
                    ).gino.status()
                    if is_group:
                        await send_goodbye(chat_id, user_id)
                        await asyncio.sleep(0.2)
                for user_id in users_found:
                    await send_hello(chat_id, user_id, user_id, is_group)
                    await asyncio.sleep(0.2)
                users_admins = [(2 if "is_owner" in x else 1 if "is_admin" in x else 0,
                                 datetime.datetime.fromtimestamp(x['join_date']), x['invited_by'],
                                 x['member_id'], chat_id) for x in response['items']]
                for data in users_admins:
                    admin, joined_at, invited_by, user_id, chat_id = data
                    await db.UserToChat.update.values(
                        admin=admin, joined_at=joined_at, invited_by=invited_by).where(
                        and_(db.UserToChat.user_id == user_id, db.UserToChat.chat_id == chat_id)
                    ).gino.scalar()


async def load_punisments() -> NoReturn:
    """Загружает все наказания"""
    punishments = await db.select([db.Punishment.id, db.Punishment.closing_at]).where(
        not_(db.Punishment.closing_at.is_(None))).gino.all()
    for punishment in punishments:
        asyncio.get_event_loop().create_task(waiting_punishment(punishment.id, punishment.closing_at))


