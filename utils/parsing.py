from datetime import datetime, timedelta
from typing import Union


def parse_unix_to_date(unix_time: Union[int, float]) -> str:
    if unix_time == 0:
        return "навсегда"
    return (datetime.utcfromtimestamp(unix_time)+timedelta(hours=3)).strftime("до %d.%m.%Y %H:%M:%S МСК")
