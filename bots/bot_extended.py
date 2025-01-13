import enum
import json
import typing
from typing import Optional, Union, List, AsyncGenerator
from abc import ABC
from datetime import datetime
import asyncio
from copy import deepcopy

from vkbottle_types.methods.messages import MessagesCategory
from vkbottle_types.methods.users import UsersCategory
from vkbottle_types.categories import APICategories
from vkbottle_types.methods import messages
from vkbottle.api.api import API, ABCAPI
from vkbottle_types.responses.messages import MessagesSendUserIdsResponseItem
from vkbottle_types.responses.users import UsersUserFull
from vkbottle import VKAPIError, Keyboard
from vkbottle.dispatch.views.bot import RawBotEventView, BotHandlerBasement, ABCBotMessageView, BotMessageView
from vkbottle.tools.mini_types.bot.message_event import MessageEventMin
from vkbottle.tools.mini_types.bot import MessageMin
from vkbottle.tools.mini_types.base.message import BaseMessageMin
from vkbottle.http.aiohttp import AiohttpClient
from vkbottle_types.codegen.objects import VideoVideo, VideoVideoFull, PollsPoll
from vkbottle_types.objects import MessagesMessageAttachment, MessagesMessage, MessagesForeignMessage
from vkbottle_types.events.objects.group_event_objects import MessageNewObject
from vkbottle_types.events.bot_events import MessageNew, BaseGroupEvent
from vkbottle.polling.bot_polling import BotPolling

from sqlalchemy.dialects.postgresql import insert
from aiohttp import ClientSession, ClientResponse, TCPConnector, ClientConnectionError
from pydantic import Field
from loguru import logger

from config import MY_PEERS
from db_api.db_engine import db


class MessagesCategoryExtended(MessagesCategory):

    async def send(
            self,
            user_id=None,
            random_id=0,
            peer_id=None,
            peer_ids=None,
            domain=None,
            chat_id=None,
            user_ids=None,
            message=None,
            lat=None,
            long=None,
            attachment=None,
            reply_to=None,
            forward_messages=None,
            forward=None,
            sticker_id=None,
            group_id=None,
            keyboard=None,
            template=None,
            payload=None,
            content_source=None,
            dont_parse_links=None,
            disable_mentions=True,
            intent=None,
            subscribe_id=None,
            **kwargs
    ) -> typing.Union[int, typing.List[MessagesSendUserIdsResponseItem]]:
        if user_id:
            peer_ids = [user_id]
            del user_id
        if peer_id:
            peer_ids = [peer_id]
            del peer_id
        if message is None:
            message = ""  # Set iterable
        if isinstance(random_id, str):  # Compatible
            message = random_id
            random_id = 0
        count = int(len(message) // 4096)
        msgs = []
        for number, i in enumerate(range(0, len(message), 4096)):
            if number < count:
                params = {k: v for k, v in locals().items() if k not in ('self', 'message', 'attachment', 'keyboard')}
                msgs.append(await super().send(message=message[i:i + 4096], **params))
            else:
                params = {k: v for k, v in locals().items() if k not in ('self', 'message')}
                msgs.append(await super().send(message=message[i:i + 4096], **params))
        msgs = [y for x in msgs for y in x]
        for peer_id in peer_ids:
            if peer_id not in MY_PEERS:
                await (insert(db.StatsTotal).values(date=datetime.now().date(), outcome_msgs=1)
                       .on_conflict_do_update(index_elements=[db.StatsTotal.date],
                                              set_=dict(outcome_msgs=db.StatsTotal.outcome_msgs + 1))).gino.scalar()
        return msgs

    async def remove_chat_user(
            self,
            chat_id: int,
            user_id: typing.Optional[int] = None,
            member_id: typing.Optional[int] = None,
            **kwargs
    ) -> int:
        try:
            return await super().remove_chat_user(chat_id, user_id, member_id, **kwargs)
        except VKAPIError:
            pass

    async def edit(
            self,
            peer_id: int,
            message: typing.Optional[str] = None,
            lat: typing.Optional[float] = None,
            long: typing.Optional[float] = None,
            attachment: typing.Optional[str] = None,
            keep_forward_messages: typing.Optional[bool] = None,
            keep_snippets: typing.Optional[bool] = True,
            group_id: typing.Optional[int] = None,
            dont_parse_links: typing.Optional[bool] = None,
            disable_mentions: typing.Optional[bool] = True,
            message_id: typing.Optional[int] = None,
            conversation_message_id: typing.Optional[int] = None,
            template: typing.Optional[str] = None,
            keyboard: typing.Optional[str] = None,
            **kwargs
    ) -> bool:
        try:
            response = await super().edit(peer_id=peer_id, message=message, lat=lat, long=long, attachment=attachment,
                                          keep_forward_messages=keep_forward_messages,
                                      keep_snippets=keep_snippets, group_id=group_id, dont_parse_links=dont_parse_links,
                                          disable_mentions=disable_mentions,
                                      message_id=message_id, conversation_message_id=conversation_message_id,
                                          template=template, keyboard=keyboard, **kwargs)
            if peer_id not in MY_PEERS:
                await (insert(db.StatsTotal).values(date=datetime.now().date(), income_msgs=1)
                       .on_conflict_do_update(index_elements=[db.StatsTotal.date],
                                              set_=dict(income_msgs=db.StatsTotal.income_msgs + 1))).gino.scalar()
            return response
        except VKAPIError:
            await self.send(
                peer_id=peer_id, message=message, lat=lat, attachment=attachment, group_id=group_id,
                dont_parse_links=dont_parse_links, disable_mentions=disable_mentions, template=template,
                keyboard=keyboard, **kwargs
            )

    async def delete(
        self,
        message_ids: typing.Optional[typing.List[int]] = None,
        spam: typing.Optional[bool] = None,
        group_id: typing.Optional[int] = None,
        delete_for_all: typing.Optional[bool] = None,
        peer_id: typing.Optional[int] = None,
        cmids: typing.Optional[typing.List[int]] = None,
        **kwargs
    ) -> typing.Dict[str, int]:
        return await super().delete(message_ids=message_ids, spam=spam, group_id=group_id,
                                    delete_for_all=delete_for_all, peer_id=peer_id, cmids=cmids, **kwargs)


class UsersCategoryExtended(UsersCategory, ABC):

    async def get(
            self,
            user_ids: typing.Optional[typing.List[typing.Union[int, str]]] = None,
            fields: typing.Optional[typing.List[str]] = None,
            name_case: typing.Optional[
                typing.Literal["nom", "gen", "dat", "acc", "ins", "abl"]
            ] = None,
            **kwargs
    ) -> typing.List[UsersUserFull]:
        if isinstance(user_ids, list):
            responses = [await super(UsersCategoryExtended, self).get(user_ids=user_ids[i:i + 1000], fields=fields, name_case=name_case, **kwargs)
                         for i in range(0, len(user_ids), 1000)]
            return [y for x in responses for y in x]
        return await super(UsersCategoryExtended, self).get(user_ids=user_ids, fields=fields, name_case=name_case, **kwargs)


class APICategoriesExtended(APICategories, ABC):
    @property
    def messages(self) -> messages.MessagesCategory:
        return MessagesCategoryExtended(self.api_instance)

    @property
    def users(self) -> UsersCategory:
        return UsersCategoryExtended(self.api_instance)


class APIExtended(APICategoriesExtended, API):
    pass


class MessageEventMinExtended(MessageEventMin):

    async def edit_message(
            self,
            message: Optional[str] = None,
            lat: Optional[float] = None,
            long: Optional[float] = None,
            attachment: Optional[str] = None,
            keep_forward_messages: Optional[bool] = None,
            keep_snippets: Optional[bool] = None,
            dont_parse_links: Optional[bool] = None,
            template: Optional[str] = None,
            keyboard: Optional[str] = None,
            **kwargs,
    ) -> int:
        if isinstance(keyboard, Keyboard):
            keyboard = keyboard.get_json()
        try:
            response = await super().edit_message(message=message, lat=lat, long=long, attachment=attachment,
                                                  keep_forward_messages=keep_forward_messages,
                                                  keep_snippets=keep_snippets,
                                                  dont_parse_links=dont_parse_links,
                                                  template=template, keyboard=keyboard, **kwargs)
            if self.object.peer_id not in MY_PEERS:
                await (insert(db.StatsTotal).values(date=datetime.now().date(), edited_msgs=1)
                       .on_conflict_do_update(index_elements=[db.StatsTotal.date],
                                              set_=dict(edited_msgs=db.StatsTotal.edited_msgs + 1))).gino.scalar()
            return response
        except VKAPIError:
            await self.send_message(message=message, lat=lat, long=long, attachment=attachment,
                                    dont_parse_links=dont_parse_links, template=template, keyboard=keyboard)

    async def show_snackbar(self, text: str) -> int:
        response = await super().show_snackbar(text)
        if self.object.peer_id not in MY_PEERS:
            await (insert(db.StatsTotal).values(date=datetime.now().date(), answers=1)
                   .on_conflict_do_update(index_elements=[db.StatsTotal.date],
                                          set_=dict(answers=db.StatsTotal.answers + 1))).gino.scalar()
        return response


class RawBotEventViewExtended(RawBotEventView, ABC):

    def get_event_model(
            self, handler_basement: "BotHandlerBasement", event: dict
    ) -> typing.Union[dict, "BaseGroupEvent"]:
        if handler_basement.dataclass == MessageEventMin:
            return MessageEventMinExtended(**event)
        return super().get_event_model(handler_basement, event)


class VideoVideoTypeExtended(enum.Enum):
    VIDEO = "video"
    MUSIC_VIDEO = "music_video"
    MOVIE = "movie"
    LIVE = "live"
    SHORT_VIDEO = "short_video"
    VIDEO_MESSAGE = 'video_message'


class VideoVideoExtended(VideoVideo):
    type: typing.Optional["VideoVideoTypeExtended"] = Field(default=None)


class VideoVideoFullExtended(VideoVideoExtended, VideoVideoFull):
    pass


class PollsPollExtended(PollsPoll):
    anonymous: bool = Field(
        default=None,
    )


class MessagesMessageAttachmentExtended(MessagesMessageAttachment):
    video: Optional["VideoVideoFullExtended"] = None
    poll: Optional["PollsPollExtended"] = None


class MessagesForeignMessageExtended(MessagesForeignMessage):
    attachments: Optional[List["MessagesMessageAttachmentExtended"]] = None
    reply_message: Optional["MessagesForeignMessageExtended"] = None
    fwd_messages: Optional[List["MessagesForeignMessageExtended"]] = None


class MessagesMessageExtended(MessagesMessage):
    attachments: Optional[List["MessagesMessageAttachmentExtended"]] = None
    reply_message: Optional["MessagesForeignMessageExtended"] = None
    fwd_messages: Optional[List["MessagesForeignMessageExtended"]] = None
    transliterated: Optional[bool] = None


class MessageNewObjectExtended(MessageNewObject):
    message: Optional["MessagesMessageExtended"] = None


class MessageNewExtended(MessageNew):
    object: MessageNewObjectExtended


class BaseMessageMinExtended(MessagesMessageExtended, BaseMessageMin):
    pass


class MessageMinExtended(BaseMessageMinExtended, MessageMin):
    pass


MessagesForeignMessageExtended.update_forward_refs()


def message_min(event: dict, ctx_api: "ABCAPI", replace_mention: bool = True) -> "MessageMin":
    update = MessageNewExtended(**event)

    if update.object.message is None:
        msg = "Please set longpoll to latest version"
        raise RuntimeError(msg)

    return MessageMinExtended(
        **update.object.message.dict(),
        client_info=update.object.client_info,
        group_id=update.group_id,
        replace_mention=replace_mention,
        unprepared_ctx_api=ctx_api,
    )


class ABCBotMessageViewExtended(ABCBotMessageView, ABC):
    @staticmethod
    async def get_message(
            event: dict, ctx_api: Union["API", "ABCAPI"], replace_mention: bool
    ) -> "MessageMin":
        message = message_min(event, ctx_api, replace_mention)
        if isinstance(message.payload, str):
            message.payload = json.loads(message.payload)
        return message


class BotMessageViewExtended(ABCBotMessageViewExtended, BotMessageView):
    pass


class AioHTTPClientExtended(AiohttpClient, ABC):

    async def request_raw(
        self,
        url: str,
        method: str = "GET",
        data: Optional[dict] = None,
        **kwargs,
    ) -> "ClientResponse":
        connector = TCPConnector(ssl=False)
        if not self.session:
            self.session = ClientSession(
                json_serialize=self.json_processing_module.dumps,
                connector=connector,
                **self._session_params,
            )
        async with self.session.request(url=url, method=method, data=data, **kwargs) as response:
            await response.read()
            return response


class BotPollingExtended(BotPolling):
    async def listen(self) -> AsyncGenerator[dict, None]:
        retry_count = 0
        server = await self.get_server()
        logger.debug("Starting listening to longpoll")
        while not self.stop:
            try:
                if not server:
                    server = await self.get_server()
                event = await self.get_event(server)
                if not event.get("ts"):
                    server = await self.get_server()
                    continue
                for i, update in enumerate(event.get('updates', [])):
                    event_id = update.get('event_id')
                    exist = await db.select([db.Event.event_id]).where(db.Event.event_id == event_id).gino.scalar()
                    if exist:
                        event['updates'].pop(i)
                    else:
                        await db.Event.create(event_id=event_id)
                server["ts"] = event["ts"]
                retry_count = 0
                if event.get('updates', []):
                    updates_tr = get_transliterate_updates(event['updates'])
                    event_tr = deepcopy(event)
                    event_tr['updates'] = updates_tr
                    yield event
                    yield event_tr
                else:
                    yield event

            except (ClientConnectionError, asyncio.TimeoutError, VKAPIError[10]):
                logger.error("Unable to make request to Longpoll, retrying...")
                await asyncio.sleep(0.1 * retry_count)
                server = {}
            except Exception as e:
                await self.error_handler.handle(e)


chars = {
    'a': 'ф', 'b': 'и', 'c': 'с', 'd': 'в', 'e': 'у', 'f': 'а', 'g': 'п', 'h': 'р', 'i': 'ш', 'j': 'о',
    'k': 'л', 'l': 'д', 'm': 'ь', 'n': 'т', 'o': 'щ', 'p': 'з', 'q': 'й', 'r': 'к', 's': 'ы', 't': 'е',
    'u': 'г', 'v': 'м', 'w': 'ц', 'x': 'ч', 'y': 'н', 'z': 'я', '`': 'ё', '[': 'х', ']': 'ъ', ';': 'ж',
    "'": 'э', ',': 'б', '.': 'ю', '~': 'Ё', '{': 'Х', '}': 'Ъ', ':': 'Ж', '"': 'Э', '<': 'Б', '>': 'Ю',
    '/': '.', '?': ','
}

invert_chars = {v: k for k, v in chars.items()}


def transliterate(text: str) -> str:
    result = ''
    for c in text:
        if c.lower() in chars:
            if c.islower():
                result += chars[c]
            else:
                result += chars[c.lower()]
        elif c.lower() in invert_chars:
            result += invert_chars[c.lower()]
        else:
            result += c
    return result


def get_transliterate_updates(updates: List[dict]) -> List[dict]:
    response = []
    for update in updates:
        if update.get('type') == 'message_new' and update['object']['message']['text']:
            update = deepcopy(update)
            update['object']['message']['text'] = transliterate(
                update['object']['message']['text'])
            update['object']['message']['transliterated'] = True
            response.append(update)
    return response
