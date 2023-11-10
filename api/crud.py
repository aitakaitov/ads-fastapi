from sqlalchemy.orm import Session

from . import models
from typing import List


def get_page(db: Session, url: str) -> models.PageInfo | None:
    return db.query(models.PageInfo).filter(models.PageInfo.url == url).first()


def add_page(db: Session, is_advertisement: bool, url: str) -> models.PageInfo:
    page_info = models.PageInfo(url=url, id_advertisement=is_advertisement)
    db.add(page_info)
    db.commit()
    db.refresh(page_info)
    return page_info


def get_rationales(db: Session, url: str) -> List[models.Rationale] | None:
    page_info = get_page(db, url)
    if not page_info:
        return None

    return list(page_info.rationales)


def add_rationales(db: Session, rationales: List[str], url: str) -> None:
    for rationale in rationales:
        db_rationale = models.Rationale(text=rationale, page_url=url)
        db.add(db_rationale)
    db.commit()
