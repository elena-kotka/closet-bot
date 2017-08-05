# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from . import Base


class Suit(Base):
    __tablename__ = 'suit'
    count = Column(Integer, default=1)
    rack_description = Column(String, default='')

    # Foreign keys
    identity_name = Column(String, ForeignKey('identity.name'), primary_key=True)
    identity = relationship('Identity', foreign_keys=[identity_name])

    def __init__(self, *args, **kwargs):
        super(Suit, self).__init__(*args, **kwargs)
