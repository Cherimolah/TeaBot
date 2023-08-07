import json
from typing import List, Union

from vkbottle.bot import Bot, Message, MessageEvent
from db_api.db_engine import db
from keyboards.private import main_kb
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from vkbottle import VKAPIError, ShowSnackbarEvent

from config import MY_PEERS


class MyBot(Bot):
    """
    Расширение класса Bot для того, чтобы отслеживать статистику по отправлениям сообщения
    """

    async def reply_msg(self, m: Message, message: str = None, attachment: str = None,
                        keyboard: str = None, disable_mentions: bool = True):
        forward = {"peer_id": m.peer_id, "conversation_message_ids": [m.conversation_message_id], "is_reply": 1}
        return await self.write_msg(m.peer_id, message, attachment, keyboard, disable_mentions, forward)

    async def write_msg(self, peer_id: Union[int, List[int]], message: str = None, attachment: str = None, keyboard: str = None,
                        disable_mentions: bool = True, forward: dict = None):
        if keyboard is None and peer_id < 2000000000:
            keyboard = main_kb
        if peer_id not in MY_PEERS:
            await (insert(db.StatsTotal).values(date=datetime.now().date(), outcome_msgs=1)
                   .on_conflict_do_update(index_elements=[db.StatsTotal.date],
                                          set_=dict(outcome_msgs=db.StatsTotal.outcome_msgs + 1))).gino.scalar()
        for i in range(0, len(message), 4096):
            message = await self.api.messages.send(peer_ids=peer_id, message=message[i:(i+1)*4096], attachment=attachment,
                                         keyboard=keyboard, random_id=0, disable_mentions=disable_mentions,
                                         forward=json.dumps(forward) if forward else None)
        return message

    async def edit_msg(self, m: Message, text: str = None, attachment: str = None,
                       keyboard: str = None, disable_mentions: bool = True, keep_forward=True):
        await self.api.messages.edit(peer_id=m.peer_id, message=text, attachment=attachment, keyboard=keyboard,
                                     conversation_message_id=m.conversation_message_id,
                                     disable_mentions=disable_mentions, keep_forward_messages=keep_forward)
        if m.peer_id not in MY_PEERS:
            await (insert(db.StatsTotal).values(date=datetime.now().date(), income_msgs=1)
                   .on_conflict_do_update(index_elements=[db.StatsTotal.date],
                                          set_=dict(income_msgs=db.StatsTotal.income_msgs + 1))).gino.scalar()

    async def send_ans(self, event: MessageEvent, message: str):
        await self.api.messages.send_message_event_answer(event.object.event_id, event.object.user_id,
                                                          event.object.peer_id,
                                                          ShowSnackbarEvent(text=message).json())
        if event.object.peer_id not in MY_PEERS:
            await (insert(db.StatsTotal).values(date=datetime.now().date(), answers=1)
                   .on_conflict_do_update(index_elements=[db.StatsTotal.date],
                                          set_=dict(answers=db.StatsTotal.answers + 1))).gino.scalar()

    async def change_msg(self, event: MessageEvent, text: str = None, attachment: str = None,
                         keyboard: str = None, disable_mentions: bool = True, keep_forward=True):
        try:
            await self.api.messages.edit(peer_id=event.object.peer_id,
                                       conversation_message_id=event.object.conversation_message_id,
                                       message=text, attachment=attachment, keyboard=keyboard,
                                     disable_mentions=disable_mentions, keep_forward_messages=keep_forward)
        except VKAPIError:
            await self.write_msg(event.peer_id, text, attachment, keyboard, disable_mentions)
        if event.object.peer_id not in MY_PEERS:
            await (insert(db.StatsTotal).values(date=datetime.now().date(), edited_msgs=1)
                   .on_conflict_do_update(index_elements=[db.StatsTotal.date],
                                          set_=dict(edited_msgs=db.StatsTotal.edited_msgs + 1))).gino.scalar()

