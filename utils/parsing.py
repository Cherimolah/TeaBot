from datetime import datetime, timedelta
from typing import Union


def parse_unix_to_date(unix_time: Union[int, float]) -> str:
    return (datetime.utcfromtimestamp(unix_time)+timedelta(hours=3)).strftime("%d.%m.%Y %H:%M:%S МСК")
