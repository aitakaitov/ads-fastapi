from pydantic import BaseModel
from typing import List


class Page(BaseModel):
    text: str
    url: str


class Url(BaseModel):
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


class PageToRender(BaseModel):
    html: str


class EntityInfo(BaseModel):
    short_text: str
    entity: str


class CookiesAnalysis(BaseModel):
    url: str
    entities: list[EntityInfo]
    page_to_render: PageToRender


class SelectEntityRequest(BaseModel):
    url: str
    selected_entity: str
