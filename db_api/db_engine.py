import asyncio
from enum import Enum
from typing import List, NoReturn
from datetime import datetime

from gino import Gino
from vkbottle_types.codegen.objects import MessagesConversationMember
from sqlalchemy import Column, BigInteger, ARRAY, VARCHAR, SmallInteger, DECIMAL, Boolean, Integer, sql, Index, Text, JSON
from sqlalchemy import ForeignKey, TIMESTAMP, Date, and_
from sqlalchemy.dialects.postgresql import insert

from config import USER, PASSWORD, HOST, DATABASE
from utils.parsing import collect_names, convert_date


class Punishments(Enum):
    MUTE = 1
    WARN = 2
    BAN = 3


class MyDatabase(Gino):
    """
    Класс-одиночка базы данных
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *args, **kwargs):
        """
        Инициализация моделей базы данных
        :param args: Аргументы для поддержки наследования класса gino.Gino
        :param kwargs: Аргументы для поддержки наследования класса gino.Gino
        """

        super().__init__(*args, **kwargs)

        class User(self.Model):
            __tablename__ = 'users'
            query: sql.Select

            user_id = Column(BigInteger, primary_key=True)
            names = Column(ARRAY(VARCHAR(60)))
            screen_name = Column(VARCHAR(60))
            sex = Column(SmallInteger)
            nickname = Column(VARCHAR(30))
            kombucha = Column(DECIMAL, nullable=False, default=0)
            kombucha_date = Column(TIMESTAMP, default=datetime.now)
            ext_nick = Column(Boolean, default=False)
            balance = Column(Integer, default=0)
            description = Column(VARCHAR(256))
            boost_kombucha = Column(Boolean, default=False)
            birthday = Column(Date)
            reaction = Column(Integer)
            dollars = Column(Integer, server_default="4999")
            win_dollars = Column(Integer, server_default="0")
            wins = Column(Integer, server_default="0")

            _idx = Index("users_ids_idx", "user_id")

        self.User = User

        class Chat(self.Model):
            __tablename__ = 'chats'
            query: sql.Select

            chat_id = Column(Integer, primary_key=True)
            hello_msg = Column(Text)
            bye_msg = Column(Text)
            rules = Column(Text)
            is_group = Column(Boolean)
            last_user_id = Column(BigInteger, default=0)

            _idx = Index("chats_idx", "chat_id")

        self.Chat = Chat

        class UserToChat(self.Model):
            __tablename__ = 'users_to_chats'
            query: sql.Select

            user_id = Column(BigInteger, ForeignKey('users.user_id'))
            chat_id = Column(Integer, ForeignKey('chats.chat_id'))
            admin = Column(SmallInteger, default=0)
            rang = Column(SmallInteger, default=0)
            invited_by = Column(BigInteger)
            joined_at = Column(TIMESTAMP)
            in_chat = Column(Boolean, default=True)

        self.UserToChat = UserToChat

        class Punishment(self.Model):
            __tablename__ = 'punishments'
            query: sql.Select

            id = Column(Integer, primary_key=True)
            type = Column(SmallInteger)
            chat_id = Column(ForeignKey('chats.chat_id'))
            created_at = Column(TIMESTAMP, default=datetime.now())
            closing_at = Column(TIMESTAMP)
            from_user_id = Column(BigInteger, ForeignKey('users.user_id'))
            to_user_id = Column(BigInteger, ForeignKey('users.user_id'))

        self.Punishment = Punishment

        class StatsTotal(self.Model):
            __tablename__ = 'stats_total'
            query: sql.Select

            date = Column(Date, primary_key=True)
            income_msgs = Column(Integer, default=0)
            outcome_msgs = Column(Integer, default=0)
            edited_msgs = Column(Integer, default=0)
            answers = Column(Integer, default=0)

        self.StatsTotal = StatsTotal

        class RPCommand(self.Model):  # Представлена лишь модель. Загрузка отдельно
            __tablename__ = 'rp_commands'
            query: sql.Select

            id = Column(Integer, primary_key=True)
            command = Column(VARCHAR(20))
            emoji = Column(VARCHAR(2))
            action = Column(VARCHAR(50))
            wom_action = Column(VARCHAR(50))
            specify = Column(VARCHAR(15))
            name_case = Column(SmallInteger)
            owner = Column(BigInteger)
            photos = Column(ARRAY(VARCHAR(100)))

        self.RPCommand = RPCommand

        class Prediction(self.Model):  # Представлена лишь модель. Загрузка отдельно
            __tablename__ = 'predictions'
            query: sql.Select

            id = Column(Integer, primary_key=True)
            figure_name = Column(VARCHAR(60))
            picture = Column(VARCHAR(100))
            mean = Column(VARCHAR(500))

        self.Prediction = Prediction

        class Aesthetic(self.Model):
            __tablename__ = 'aesthetics'
            query: sql.Select

            id = Column(Integer, primary_key=True)
            photo = Column(VARCHAR(100))

        self.Aesthetic = Aesthetic

        class Sticker(self.Model):
            __tablename__ = 'stickers'

            id = Column(Integer, primary_key=True)
            name = Column(Text)
            price = Column(Integer, default=0)

        self.Sticker = Sticker

        class Event(self.Model):
            __tablename__ = 'events'

            event_id = Column(Text, unique=True)

        self.Event = Event

        class Message(self.Model):
            __tablename__ = "messages"

            id = Column(Integer, primary_key=True)
            text = Column(Text)

        self.Message = Message

        class RouletteGame(self.Model):
            __tablename__ = 'roulette_games'

            id = Column(Integer, primary_key=True)
            player_1 = Column(BigInteger, ForeignKey('users.user_id'), on_delete='CASCADE')
            player_2 = Column(BigInteger, ForeignKey('users.user_id'), on_delete='CASCADE')
            items = Column(JSON)
            step = Column(Integer)
            lives_1 = Column(Integer)
            lives_2 = Column(Integer)
            round_number = Column(Integer)
            tea = Column(Integer)
            coffee = Column(Integer)

        self.RouletteGame = RouletteGame

    async def connect(self):
        """Подключение к базе данных"""
        await self.set_bind(f"postgresql://{USER}:{PASSWORD}@{HOST}/{DATABASE}")
        await self.gino.create_all()

    async def is_chat_registered(self, chat_id: int) -> bool:
        """Проверяет зарегистрирован ли чат"""
        return bool(await self.Chat.query.where(self.Chat.chat_id == chat_id).gino.first())

    async def register_chat(self, chat_id: int, members: List[MessagesConversationMember], users_responses) -> NoReturn:
        """
        Регистрация чата
        Уровни администрации пользователей:
        2 - создатель, 1 - администратор, 0 -обычный пользователь.
        По умолчанию создателю даётся ранг 5, админам ранг 4
        """
        await self.Chat.create(chat_id=chat_id, is_group=members[0].member_id < 0 and members[0].is_owner)
        users_info = [{"user_id": x.id, "names": collect_names(x), "sex": x.sex, "birthday": convert_date(x.bdate),
                       "screen_name": x.screen_name or f"id{x.id}"} for x in users_responses]
        await insert(self.User).values(users_info).on_conflict_do_nothing().gino.scalar()

        # Записываем информацию о пользователях в чате
        users_chat_info = [(x.member_id, chat_id, 2 if x.is_owner else 1 if x.is_admin else 0, 5 if x.is_owner else 4
        if x.is_admin else 0, x.invited_by, datetime.utcfromtimestamp(x.join_date))
                           for x in members if x.member_id > 0]
        await insert(self.UserToChat).values(users_chat_info).gino.scalar()

    async def is_higher(self, chat_id: int, from_user_id: int, to_user_id: int) -> bool:
        """Проверяет выше ли пользователь по рангу"""
        from_user_admin, from_user_rang = await self.UserToChat.select('admin', 'rang').where(
            and_(self.UserToChat.user_id == from_user_id, self.UserToChat.chat_id == chat_id)
        ).gino.first()
        to_user_admin, to_user_rang = await self.UserToChat.select('admin', 'rang').where(
            and_(self.UserToChat.user_id == to_user_id, self.UserToChat.chat_id == chat_id)
        ).gino.first()
        return from_user_admin > to_user_admin or from_user_rang > to_user_rang

    async def get_mention_user(self, user_id: int, name_case: int) -> str:
        """Возвращает строку упоминание пользователя по айди и нужному падежу"""
        names, nickname = await self.User.select('names', 'nickname').where(
            self.User.user_id == user_id
        ).gino.first()
        return f"[id{user_id}|{names[name_case] if nickname is None else nickname}]"

    async def is_admin_user(self, user_id: int, chat_id: int) -> bool:
        """Проверяет является ли пользователь администратором"""
        admin = await self.UserToChat.select('admin').where(
            and_(self.UserToChat.user_id == user_id, self.UserToChat.chat_id == chat_id)
        ).gino.scalar()
        return admin > 0

    async def is_woman_user(self, user_id: int) -> bool:
        """Проверяет является ли пользователь женского пола. Нужно для добавления 'а' в конце, например в рп-командах"""
        sex = await self.User.select('sex').where(
            self.User.user_id == user_id
        ).gino.scalar()
        return sex == 1

    async def is_user_in_chat(self, user_id: int, chat_id: int) -> bool:
        """Проверяет находится ли пользователь в чате"""
        return await self.select([self.UserToChat.in_chat]).where(
            and_(self.UserToChat.user_id == user_id, self.UserToChat.chat_id == chat_id)
        ).gino.scalar()

    async def add_punishment(self, type_pun: Punishments, to_time: int, chat_id: int, from_user_id: int,
                             to_user_id: int) -> NoReturn:
        """Записывает наказание пользователю"""
        pun = await self.Punishment.create(type=type_pun.value, chat_id=chat_id, to_user_id=to_user_id,
                                           closing_at=datetime.utcfromtimestamp(to_time) if to_time else None,
                                           from_user_id=from_user_id,
                                           )
        if to_time:
            from utils.views import waiting_punishment
            asyncio.get_event_loop().create_task(waiting_punishment(pun.id, to_time))
        return pun


db = MyDatabase()
