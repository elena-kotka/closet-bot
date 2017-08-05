# -*- coding: utf-8 -*-
import os
import contextlib
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models

logger = logging.getLogger(__name__)


def connect(db_uri=None):
    if not db_uri:
        db_uri = os.environ.get('CLOSET_BOT_DB_URI', None)

    if not db_uri:
        raise ValueError("No database URI specified.")

    engine = create_engine(db_uri)
    models.Base.metadata.drop_all(engine)
    models.Base.metadata.create_all(engine)
    return engine


def get_session(db_connection):
    session_maker = sessionmaker(bind=db_connection)
    session = session_maker()
    return session


@contextlib.contextmanager
def scoped_session(db_connection):
    session_maker = sessionmaker(bind=db_connection)
    session = session_maker()
    try:
        yield session
    finally:
        session.commit()
