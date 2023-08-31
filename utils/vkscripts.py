from typing import List
from loader import bot
import json

from aiohttp import ClientSession
from vkbottle_types.responses.users import UsersUserFull


async def get_cases_users(user_ids: List[int]) -> List[UsersUserFull]:
    name_cases = ("nom", "gen", "dat", "acc", "ins", "abl")
    fields = [f"first_name_{x},last_name_{x}" for x in name_cases]
    fields.append("sex,screen_name,bdate")
    return await bot.api.users.get(user_ids=user_ids, fields=fields)


async def get_conversations_members(peer_ids: List[int]) -> dict:
    requirements = [{"peer_id": peer_id} for peer_id in peer_ids]
    requests = []
    for request in requirements:
        requests.append(f"[API.messages.getConversationMembers({json.dumps(request)}), {request['peer_id']}]")
    code = f'return [{",".join(requests)}];'
    url = f"{bot.api.API_URL}/execute"
    async with ClientSession() as session:
        response = await session.get(url, params={"code": code,
                                                  "v": bot.api.API_VERSION,
                                                  "access_token": await bot.api.token_generator.get_token()})
        data = await response.json(encoding="utf-8")
    if False in data['response']:
        data['response'].remove(False)
    return data['response']

