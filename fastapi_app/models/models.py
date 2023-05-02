from pydantic import BaseModel, Field
from typing import List


class User(BaseModel):
    user_id: int
    user_name: str | None
    n_pairs: int = Field(ge=3)


class Pair(BaseModel):
    coin_id: str
    vs_currency: str
