from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, PickleType, Text
from sqlalchemy.orm import relationship

from .database import Base


class PageInfo(Base):
    __tablename__ = 'pages'

    url = Column(
        'url',
        String(2000),
        primary_key=True,
        index=True
    )

    is_advertisement = Column(
        'is_advertisement',
        Boolean
    )

    rationales = relationship('Rationale', back_populates='page')

    minhash = Column(
        'minhash',
        PickleType()
    )


class Rationale(Base):
    __tablename__ = 'rationales'

    id = Column(
        'id',
        Integer,
        unique=True,
        primary_key=True,
        autoincrement=True
    )

    text = Column(
        'text',
        String(2500),
    )

    page_url = Column(String(2000), ForeignKey('pages.url'), index=True)

    page = relationship('PageInfo', back_populates='rationales')


class DomainUrl(Base):
    __tablename__ = 'domain_cache'

    domain = Column(
        'domain',
        String(2500),
        unique=True,
        primary_key=True
    )

    cookie_url = Column(
        'cookie_url',
        String(2500),
    )


class CookiesAnalysis(Base):
    __tablename__ = 'cookies_analysis'

    url = Column(
        'url',
        String(2500),
        unique=True,
        primary_key=True
    )

    minhash = Column(
        'minhash',
        PickleType()
    )

    processed_html = Column(
        'processed_html',
        Text()
    )

    # contains a list of entities
    # entity['type'] = which entity
    # entity['attribute'] = what attribute do the end and start elements have
    # entity['attr_start_value'] = what value does the start element attribute have
    # entity['attr_end_value'] = what value does the end element attribute have
    # entity['start_offset'] = offset in characters in the start element
    # entity['end_offset'] = offset in characters in the end element
    entity_data_json = Column(
        'entity_data',
        Text()
    )