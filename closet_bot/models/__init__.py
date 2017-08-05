# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from .identity import Identity
from .suit import Suit
from .patron import Patron
