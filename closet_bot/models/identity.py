# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from datetime import datetime
from . import Base


class Identity(Base):
    __tablename__ = 'identity'
    name = Column(String, primary_key=True)
    display_name = Column(String)
    avatar = Column(String, default=None)
    reference = Column(String, default=None)
    last_seen = Column(DateTime, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super(Identity, self).__init__(*args, **kwargs)

    def __str__(self):
        return "Identity: {0}".format(self.name)
