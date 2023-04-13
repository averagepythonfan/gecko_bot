from pydantic import BaseModel
from .models import UserResponse
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
