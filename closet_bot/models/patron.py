# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base


class Patron(Base):
    __tablename__ = 'patron'
    id = Column(String, primary_key=True)
    credit = Column(Float, default=0.00)
    greeted = Column(Boolean, default=False)

    speaking_with = Column(String, default='')

    # Foreign keys
    identity_name = Column(String, ForeignKey('identity.name'))
    identity = relationship('Identity', foreign_keys=identity_name, backref='identity')

    suit_identity_name = Column(String, ForeignKey('suit.identity_name'))
    suit = relationship('Suit', foreign_keys=suit_identity_name, backref='suit_identity_name')

    def __init__(self, *args, **kwargs):
        super(Patron, self).__init__(*args, **kwargs)