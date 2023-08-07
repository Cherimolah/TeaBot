from loader import bot
from vkbottle import PhotoMessageUploader, DocMessagesUploader


bot_photo_message_upl = PhotoMessageUploader(bot.api)
bot_doc_message_upl = DocMessagesUploader(bot.api)
