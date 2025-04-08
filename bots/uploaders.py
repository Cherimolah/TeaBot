import asyncio
from typing import Union, List

from vkbottle import VKAPIError, PhotoMessageUploader, DocMessagesUploader, VideoUploader

from loader import bot, ilya


class MyPhotoMessageUploader(PhotoMessageUploader):

    def __init__(self,
                 api=None,
                 api_getter=None,
                 ):
        super().__init__(api, api_getter)

    async def upload(self, file_source, **params) -> Union[str, List[dict]]:
        while True:
            try:
                return await super().upload(file_source, **params)
            except VKAPIError:
                await asyncio.sleep(0.2)


bot_photo_message_upl = MyPhotoMessageUploader(api=bot.api)
bot_doc_message_upl = DocMessagesUploader(api=bot.api)
ilya_video_upl = VideoUploader(api=ilya.api)
