from datetime import datetime, timedelta, date
from typing import Union, List
from vkbottle.bot import Message
import re
import time
from vkbottle_types.responses.users import UsersUserFull


mention_regex = re.compile(r"^\[(?P<type>id|club|public)(?P<id>\d*)\|(?P<text>.+)\]$")
link_regex = re.compile(r"^https:/(?P<type>/|/m.)vk.com/(?P<screen_name>\w*)$")


def parse_unix_to_date(unix_time: Union[int, float, datetime]) -> str:
    if unix_time is None:
        return "навсегда"
    if isinstance(unix_time, (int, float)):
        return f'[{(datetime.utcfromtimestamp(unix_time)+timedelta(hours=3)).strftime("%d.%m.%Y %H:%M:%S МСК")}]'
    return f'[{unix_time.strftime("%d.%m.%Y %H:%M:%S МСК")}]'


years = [
    "год", "года", "лет"
]
months = [
    "мес", "месяцев", "месяц", "месяца"
]
weeks = [
    "неделя", "недель", "недели"
]
days = [
    "день", "дня", "дней", "день"
]
hours = [
    "час", "часа", "часов"
]
minutes = [
    "минуты", "мин", "минут", "мин"
]
seconds = [
    "сек", "секунды", "сек", "секунда", "секунд", "секунду"
]


# Функция для определения срока из текста. Возвращает значение в секундах. 0 если навсегда. -1 Если неверные данные
def parse_period(m: Message) -> int:
    params = m.text.lower().split(" ")
    if len(params) == 1 or params[1] == "навсегда":
        return 0
    params = params[1:]
    if params[-1].isdigit():
        params = params[:-1]
    if re.search(mention_regex, params[0]) is not None or re.search(link_regex, params[0]) is not None:
        params = params[1:]
    last_number = 0
    total = 0
    for index, param in enumerate(params):
        if index % 2 == 0:
            if not param.isdigit():
                return -1
            last_number = int(param)
        else:
            if param.isdigit():
                return -1
            if param in years:
                total += last_number * 31536000
            elif param in months:
                total += last_number * 2592000
            elif param in weeks:
                total += last_number * 604800
            elif param in days:
                total += last_number * 86400
            elif param in hours:
                total += last_number * 3600
            elif param in minutes:
                total += last_number * 60
            elif param in seconds:
                total += last_number
            last_number = 0
    return total + int(time.time()) if total > 0 else None


def get_count_page(count_orders: int, step: int) -> int:
    if count_orders % step == 0:
        return count_orders // step
    return (count_orders // step) + 1


def parse_cooldown(cooldown: float) -> str:
    hours = int(cooldown // 3600)
    minutes = int((cooldown - hours * 3600) // 60)
    seconds = int(cooldown - hours * 3600 - minutes * 60)
    return f"{hours} час(-a, -ов) {minutes} минут {seconds} секунд"


# Функция для сбора имён и фамилий по падежам
def collect_names(user: UsersUserFull) -> List[str]:
    name_cases = ("nom", "gen", "dat", "acc", "ins", "abl")
    return [f"{user.__getattribute__(f'first_name_{x}')} {user.__getattribute__(f'last_name_{x}')}" for x in
            name_cases]


def convert_date(bdate: str):
    """
    Метод для преобразования вкшной строки даты рождения в объект date
    Пример: "11.09.2001" -> "2001.09.11" в виде объекта date
    :param bdate: вкшная строка с датой рождения
    :return: объект date с датой рождения
    """
    if not bdate:
        return None
    data = bdate.split(".")
    if len(data) == 2:  # Не указан год рождения
        day, month = data
        year = 1800  # Такой год будет считаться не установленным в вк
    else:
        day, month, year = data
    try:
        bdate_object = date(int(year), int(month), int(day))
        return bdate_object
    except ValueError:
        return

