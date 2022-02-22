from blueprints.blueprint import bp
from typing import List


async def get_cases_users(user_ids: List[int]) -> List[List[dict]]:
    users_string = f'"{",".join([str(x) for x in user_ids])}"'
    return (await bp.api.execute('return [API.users.get({"user_ids": ' + users_string + ','
                                 ' "fields": "sex,screen_name"})'
                                 ', API.users.get({"user_ids": '
                                 + users_string + ', "name_case": "gen"}),'
                                 ' API.users.get({"user_ids": ' + users_string +
                                 ', "name_case": "dat"}), API.users.get({"user_ids": ' +
                                 users_string + ','
                                 ' "name_case": "acc"}), API.users.get({"user_ids": ' +
                                 users_string + ','
                                 ' "name_case": "ins"}), API.users.get({"user_ids": ' +
                                 users_string + ', "name_case": "abl"})];'))['response']
