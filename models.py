from pydantic import BaseModel
from typing import List


class Page(BaseModel):
    text: str


class Classification(BaseModel):
    is_advertisement: bool


class Rationales(BaseModel):
    rationales: List[str]


class Message(BaseModel):
    code: int
    message: str