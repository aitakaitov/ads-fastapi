from sqlalchemy.orm import Session

from . import models
from typing import List
import json


def get_page(db: Session, url: str) -> models.PageInfo | None:
    return db.query(models.PageInfo).filter(models.PageInfo.url == url).first()


def add_page(db: Session, is_advertisement: bool, url: str, minhash) -> models.PageInfo:
    page_info = models.PageInfo(url=url, is_advertisement=is_advertisement, minhash=minhash)
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


def update_page_invalidate_rationales(db: Session, page_info: models.PageInfo, is_advertisement: bool, minhash):
    page_info.is_advertisement = is_advertisement
    page_info.minhash = minhash
    page_info.rationales[:] = []
    db.commit()


def add_domain_to_cache(db: Session, domain: str, cookie_url: str) -> None:
    domain_cache = models.DomainUrl(domain=domain, cookie_url=cookie_url)
    db.add(domain_cache)
    db.commit()


def update_domain_cache(db: Session, domain: str, cookie_url: str) -> bool:
    domain_cache = get_cookie_url_from_cache(db, domain)
    if not domain_cache:
        return False

    domain_cache.cookie_url = cookie_url
    db.commit()
    return True


def get_cookie_url_from_cache(db: Session, domain: str) -> models.DomainUrl | None:
    return db.query(models.DomainUrl).filter(models.DomainUrl.domain == domain).first()


def get_analysis(db: Session, url: str) -> models.CookiesAnalysis | None:
    return db.query(models.CookiesAnalysis).filter(models.CookiesAnalysis.url == url).first()


def delete_analysis(db: Session, analysis: models.CookiesAnalysis):
    db.delete(analysis)
    db.commit()


def create_analysis(db: Session, url: str, modified_html: str, entity_data: dict, minhash):
    analysis = models.CookiesAnalysis(
        url=url,
        processed_html=modified_html,
        minhash=minhash,
        entity_data_json=json.dumps(entity_data)
    )
    db.add(analysis)
    db.commit()
