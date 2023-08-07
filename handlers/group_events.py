from loader import bot
from vkbottle import GroupEventType
from vkbottle_types.events.bot_events import GroupLeave, GroupJoin, WallPostNew, LikeAdd, WallReplyNew, BoardPostNew
from config import ADMIN_ID, GROUP_ID
from db_api.db_engine import db
from vkbottle_types.objects import CallbackLikeAddRemoveObjectType as LikeType


@bot.on.raw_event(GroupEventType.GROUP_LEAVE, GroupLeave)
async def left_user(event: GroupLeave):
    await bot.write_msg(ADMIN_ID, f"Отписался от паблика: https://vk.com/id{event.object.user_id}")
    if (await bot.api.messages.is_messages_from_group_allowed(group_id=GROUP_ID, user_id=event.object.user_id)).is_allowed:
        await bot.write_msg(event.object.user_id, "👉🥺👈 Вернись, пожалуйста, я тебя прошу")


@bot.on.raw_event(GroupEventType.GROUP_JOIN, GroupJoin)
async def join_user(event: GroupJoin):
    await bot.write_msg(ADMIN_ID, f"Вступил в группу: https://vk.com/id{event.object.user_id}")


@bot.on.raw_event(GroupEventType.WALL_POST_NEW, WallPostNew)
async def new_post(event: WallPostNew):
    chat_ids = [x.chat_id + 2000000000 for x in await db.select([db.Chat.chat_id]).gino.all()]
    for i in range(0, len(chat_ids), 100):
        await bot.api.messages.send(message="⚡🔥 Новый пост в группе!",
                                        attachment=f"wall-{event.group_id}_{event.object.id}",
                                        peer_ids=chat_ids[i:i+100], random_id=0)


@bot.on.raw_event(GroupEventType.LIKE_ADD, LikeAdd)
async def like_added(event: LikeAdd):
    user = await bot.api.users.get(event.object.liker_id, fields="sex")
    object_type = event.object.object_type
    if object_type == LikeType.PHOTO:
        post_type = "фото"
    elif object_type == LikeType.POST:
        post_type = "пост"
    elif object_type == LikeType.NOTE:
        post_type = "записку"
    elif object_type == LikeType.COMMENT:
        post_type = "комментарий"
    elif object_type == LikeType.MARKET_COMMENT:
        post_type = "комментарий в магазине"
    elif object_type == LikeType.PHOTO_COMMENT:
        post_type = "комментарий под фото"
    elif object_type == LikeType.MARKET:
        post_type = "товар"
    elif object_type == LikeType.TOPIC_COMMENT:
        post_type = "комментарий под темой"
    elif object_type == LikeType.VIDEO:
        post_type = "видео"
    elif object_type == LikeType.VIDEO_COMMENT:
        post_type = "комментарий под видео"
    else:
        post_type = "неизвестным типом"
    await bot.write_msg(ADMIN_ID, f"❤ [id{user[0].id}|{user[0].first_name} {user[0].last_name}] "
                                 f"поставил{'а' if user[0].sex == 1 else ''} лайк на {post_type} "
                                 f"https://vk.com/wall-{GROUP_ID}_{event.object.object_id}")


@bot.on.raw_event(GroupEventType.WALL_REPLY_NEW, WallReplyNew)
async def comment_added(event: WallReplyNew):
    if event.object.from_id > 0:
        user = await bot.api.users.get(event.object.from_id, fields="sex")
        name = f'[id{user[0].id}|{user[0].first_name} {user[0].last_name}]'
    else:
        group = await bot.api.groups.get_by_id(abs(event.object.from_id))
        name = f'[id{group[0].id}|{group[0].name}]'
        user = None
    await bot.write_msg(ADMIN_ID, f"📝 {name} написал{'а' if user and user[0].sex == 1 else ''} под постом "
                                 f"https://vk.com/wall-{GROUP_ID}_{event.object.post_id} "
                                 f"комментарий: «{event.object.text}»")


@bot.on.raw_event(GroupEventType.BOARD_POST_NEW, BoardPostNew)
async def board_post_new(event: BoardPostNew):
    if event.object.from_id > 0:
        user = await bot.api.users.get(event.object.from_id, fields="sex")
        name = f'[id{user[0].id}|{user[0].first_name} {user[0].last_name}]'
    else:
        group = await bot.api.groups.get_by_id(abs(event.object.from_id))
        name = f'[id{group[0].id}|{group[0].name}]'
        user = None
    await bot.write_msg(ADMIN_ID, f"📝  {name} написал{'а' if user and user[0].sex == 1 else ''} в обсуждении "
                                 f"https://vk.com/topic{event.object.topic_owner_id}_{event.object.topic_id} "
                                 f"комментарий: «{event.object.text}»")
