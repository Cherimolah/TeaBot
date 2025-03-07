from typing import List
from loader import bot
import json

from vkbottle_types.responses.users import UsersUserFull

from loader import client


name_cases = ("nom", "gen", "dat", "acc", "ins", "abl")
user_fields = [f"first_name_{x},last_name_{x}" for x in name_cases]
user_fields.extend(['sex', 'bdate', 'screen_name'])


async def get_cases_users(user_ids: List[int]) -> List[UsersUserFull]:
    return await bot.api.users.get(user_ids=user_ids, fields=user_fields)


async def get_conversations_members(peer_ids: List[int]) -> dict:
    requirements = [{"peer_id": peer_id} for peer_id in peer_ids]
    requests = []
    for request in requirements:
        requests.append(f"[API.messages.getConversationMembers({json.dumps(request)}), {request['peer_id']}]")
    code = f'return [{",".join(requests)}];'
    url = f"{bot.api.API_URL}/execute"
    data = await client.request_json(url, params={"code": code,
                                                  "v": bot.api.API_VERSION,
                                                  "access_token": await bot.api.token_generator.get_token()})
    if False in data['response']:
        data['response'].remove(False)
    return data['response']
