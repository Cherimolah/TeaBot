from vkbottle.bot import Blueprint, Message, MessageEvent
from db.main_database import main_db
import json
from keyboards.private import main_kb


class MyBlueprint(Blueprint):
    async def reply_msg(self, m: Message, message: str = None, attachment: str = None,
                        keyboard: str = None, disable_mentions: bool = True):
        forward = json.dumps({"peer_id": m.peer_id, "conversation_message_ids": [m.conversation_message_id],
                              "is_reply": 1})
        if keyboard is None and m.peer_id < 2000000000:
            keyboard = main_kb
        await self.api.messages.send(message=message, attachment=attachment, keyboard=keyboard, forward=forward,
                                     random_id=0, peer_id=m.peer_id, disable_mentions=disable_mentions)
        await main_db.add_outcome("outcome_message", m.peer_id)

    async def write_msg(self, peer_id: int, message: str = None, attachment: str = None, keyboard: str = None,
                        disable_mentions: bool = True):
        if keyboard is None and peer_id < 2000000000:
            keyboard = main_kb
        await self.api.messages.send(peer_id=peer_id, message=message, attachment=attachment, keyboard=keyboard,
                                     random_id=0, disable_mentions=disable_mentions)
        await main_db.add_outcome("outcome_message", peer_id)

    async def edit_msg(self, peer_id: int, message_id: int, text: str = None, attachment: str = None,
                       keyboard: str = None, disable_mentions: bool = True):
        await self.api.messages.edit(peer_id=peer_id, message=text, attachment=attachment, keyboard=keyboard,
                                     message_id=message_id, disable_mentions=disable_mentions)
        await main_db.add_outcome("edit_message", peer_id)

    async def send_ans(self, m: MessageEvent, message: str):
        event_data = json.dumps({"type": "show_snackbar", "text": message})
        await self.api.messages.send_message_event_answer(m.event_id, m.user_id, m.peer_id, event_data)
        await main_db.add_outcome("event_answer", m.peer_id)


bp = MyBlueprint()
bp.labeler.vbml_ignore_case = True
