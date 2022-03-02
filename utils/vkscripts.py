from typing import List
from blueprints.blueprint import bp
from vkbottle.http.aiohttp import AiohttpClient
from config import BOT_TOKEN


client = AiohttpClient()


async def get_cases_users(user_ids: List[int]) -> List[List[dict]]:
    users = f'{",".join([str(x) for x in user_ids])}'
    return (await bp.api.execute(f'return [API.users.get({{"user_ids": "{users}", "fields": "sex,screen_name"}}),\n'
                                 f'API.users.get({{"user_ids": "{users}", "name_case": "gen"}}),\n'
                                 f'API.users.get({{"user_ids": "{users}", "name_case": "dat"}}),\n'
                                 f'API.users.get({{"user_ids": "{users}", "name_case": "acc"}}),\n'
                                 f'API.users.get({{"user_ids": "{users}", "name_case": "ins"}}),\n'
                                 f'API.users.get({{"user_ids": "{users}", "name_case": "abl"}})];'))['response']


async def get_conversations_members(peer_ids: List[int]) -> dict:
    code = f"""return [{','.join([f'API.messages.getConversationMembers({{"peer_id": {x}}})' for x in peer_ids])}];"""
    response = (await client.request_json(f"https://api.vk.com/method/execute?code={code}&access_token={BOT_TOKEN}&"
                                          f"v=5.144"))['response']
    return response

