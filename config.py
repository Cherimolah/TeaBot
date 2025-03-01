import os

from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
USER_TOKEN = os.environ.get('USER_TOKEN')
YOOMONEY_TOKEN = os.environ.get("YOOMONEY_TOKEN")
YOOMONEY_SECRET = os.environ.get("YOOMONEY_SECRET")
HOST = os.environ.get("HOST")
USER = os.environ.get("USER_POSTGRES")
PASSWORD = os.environ.get('PASSWORD')
DATABASE = os.environ.get('DATABASE')
MY_PEERS = list(map(int, os.environ.get('MY_PEERS').split(",")))
GROUP_ID = int(os.environ.get('GROUP_ID'))
ADMIN_ID = int(os.environ.get('ADMIN_ID'))
rangnames = [
    "«Без ранга»", "«Принцесса Нури (🌟)»", "«Ahmad Tea (🌟 🌟)»", "«Curtis (🌟 🌟 🌟)»", "«Tess (🌟 🌟 🌟 🌟)»",
    "«Greinfield (🌟 🌟 🌟 🌟 🌟)»"
]
PREFIXES = ["", "/", "!", "чай ", "tea ", "/чай ", "/tea "]
secret_key = os.environ.get('SECRET_KEY')
confirmation_code = os.environ.get('CONFIRMATION_CODE')
DATE_PARSING = os.environ.get('DATE_PARSING')
DEBUG = os.environ.get('DEBUG') == 'True'
FONT_PATH = os.environ.get('FONT_PATH')
DOMAIN = os.environ.get('DOMAIN')
GROUP_TAG = os.environ.get('GROUP_TAG')
AI_API_KEY = os.environ.get('AI_API_KEY')
