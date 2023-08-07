import os

from vkbottle_types.objects import PhotosPhoto
from aiohttp import ClientSession
import aiofiles

from bots.uploaders import bot_photo_message_upl


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
    async with ClientSession() as session:
        data = await (await session.get(url)).read()
    async with aiofiles.open(name, mode="wb") as file:
        await file.write(data)


async def re_upload_photo(photo: PhotosPhoto, name: str) -> str:
    await download_photo(photo, name)
    attachment_string = await bot_photo_message_upl.upload(name)
    os.remove(name)
    return attachment_string
