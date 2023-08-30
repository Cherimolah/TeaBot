import asyncio
from typing import Optional, Union, List

from vkbottle import VKAPIError, PhotoMessageUploader, DocMessagesUploader

from loader import bot


class MyPhotoMessageUploader(PhotoMessageUploader):

    def __init__(self,
                 api=None,
                 api_getter=None,
                 generate_attachment_strings: bool = True,
                 with_name: Optional[str] = None,
                 ):
        super().__init__(api, api_getter, generate_attachment_strings, with_name)

    async def upload(self, file_source, **params) -> Union[str, List[dict]]:
        while True:
            try:
                return await super().upload(file_source, **params)
            except VKAPIError:
                await asyncio.sleep(0.2)


bot_photo_message_upl = MyPhotoMessageUploader(bot.api)
bot_doc_message_upl = DocMessagesUploader(bot.api)
