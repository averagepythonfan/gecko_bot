import aiohttp
from pydantic import BaseModel
from typing import List


class UserResponse(BaseModel):
    _id: str
    user_id: int
    user_name: str | None
    n_pairs: int
    pairs: List[str | None] | None


def validate_user_data(input_data):
    raw = str(input_data)
    raw = raw.replace('ObjectId(', '').replace(')', '').replace("'", '"')
    valid = UserResponse.parse_raw(raw)
    return valid.dict()


async def send_pic(file_name: str, url: str):
    with open(file_name, 'rb') as img:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, data={'photo': img}) as resp:
                response = await resp.json()
                return response
