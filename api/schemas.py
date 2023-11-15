from pydantic import BaseModel
from typing import List


class Page(BaseModel):
    text: str
    url: str


class Classification(BaseModel):
    is_advertisement: bool


class Rationales(BaseModel):
    rationales: List[str]


class Message(BaseModel):
    code: int
    message: str


class DomainCacheRequest(BaseModel):
    url: str


class DomainCacheResponse(BaseModel):
    url: str
