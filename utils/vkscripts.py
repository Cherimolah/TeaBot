from typing import List, Optional
from loader import bot
import json
import os

from vkbottle_types.responses.users import UsersUserFull
from aiohttp import ClientSession

from loader import client, ilya
from config import GROUP_ID
from bots.uploaders import ilya_video_upl


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


async def reupload_video(video) -> Optional[str]:
    video = await ilya.api.video.get(videos=f"{video.owner_id}_{video.id}_{video.access_key}")
    if not video.items[0].files:
        return
    files = video.items[0].files.to_dict()
    for quality in ['2160', '1440', '1080', '720', '480', '360', '240', '144']:
        if files.get(f'mp4_{quality}'):
            url = files[f'mp4_{quality}']
            break
    else:
        return
    async with ClientSession() as session:
        response = await session.get(url)
        data = await response.read()
    with open('video.mp4', 'wb') as file:
        file.write(data)
    video = await ilya_video_upl.upload('video.mp4', is_private=True, group_id=GROUP_ID)
    os.remove('video.mp4')
    return video
