from pydantic import BaseModel, Field
from typing import List


class User(BaseModel):
    user_id: int
    user_name: str | None
    n_pairs: int = Field(ge=3)


class Pair(BaseModel):
    coin_id: str
    vs_currency: str


class UserResponse(BaseModel):
    _id: str
    user_id: int
    user_name: str | None
    n_pairs: int
    pairs: List[str | None] | None
