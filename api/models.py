from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
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
