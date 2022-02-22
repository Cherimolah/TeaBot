from vkbottle.bot import Blueprint, Message, MessageEvent
from db.main_database import main_db
from config import MY_PEERS
import json


class MyBlueprint(Blueprint):
    async def reply_msg(self, m: Message, message: str = None, attachment: str = None,
                        keyboard: str = None):
        forward = json.dumps({"peer_id": m.peer_id, "conversation_message_ids": [m.conversation_message_id],
                              "is_reply": 1})
        await self.api.messages.send(message=message, attachment=attachment, keyboard=keyboard, forward=forward,
                                     random_id=0, peer_id=m.peer_id)
        await main_db.add_outcome("outcome_messages", m.peer_id)

    async def write_msg(self, peer_id: int, message: str = None, attachment: str = None, keyboard: str = None):
        await self.api.messages.send(peer_id=peer_id, message=message, attachment=attachment, keyboard=keyboard,
                                     random_id=0)
        await main_db.add_outcome("outcome_messages", peer_id)

    async def edit_msg(self, peer_id: int, message_id: int, text: str = None, attachment: str = None,
                       keyboard: str = None):
        await self.api.messages.edit(peer_id=peer_id, message=text, attachment=attachment, keyboard=keyboard,
                                     message_id=message_id)
        await main_db.add_outcome("edited_messages", peer_id)

    async def send_ans(self, m: MessageEvent, message: str):
        event_data = json.dumps({"type": "show_snackbar", "text": message})
        await self.api.messages.send_message_event_answer(m.event_id, m.user_id, m.peer_id, event_data)
        await main_db.add_outcome("outcome_event_answers", m.peer_id)


bp = MyBlueprint()
bp.labeler.vbml_ignore_case = True
