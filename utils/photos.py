import json
import os
import base64

from vkbottle_types.objects import PhotosPhoto
import aiofiles
from aiohttp import ClientSession

from bots.uploaders import bot_photo_message_upl
from loader import client
from config import PHOTO_HOST_TOKEN


def get_max_photo(photo: PhotosPhoto) -> str:
    max_square = 0
    url = ""
    for size in photo.sizes:
        if size.height * size.width > max_square:
            max_square = size.height * size.width
            url = size.url
    return url


async def download_photo(photo: PhotosPhoto, name: str):
    url = get_max_photo(photo)
    data = await client.request_content(url)
    async with aiofiles.open(name, mode="wb") as file:
        await file.write(data)


async def re_upload_photo(photo: PhotosPhoto, name: str) -> str:
    await download_photo(photo, name)
    attachment_string = await bot_photo_message_upl.upload(name)
    os.remove(name)
    return attachment_string


async def upload_host_photo(file_name: str) -> str:
    async with aiofiles.open(file_name, mode="rb") as file:
        data = await file.read()
    content = base64.b64encode(data).decode('utf-8')
    async with ClientSession() as session:
        response = await session.post('https://img.cherimoladev.ru/upoload',
                                      data=json.dumps({"photo": content, "name": file_name}),
                                      headers={"Authorization": PHOTO_HOST_TOKEN})
        return (await response.json())['url']
