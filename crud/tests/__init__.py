# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from unittest import TestCase

from paste.deploy import loadapp
from paste.script.appinstall import SetupCommand

import crud


Base = declarative_base()

def setUp():
    DB_STRING = 'sqlite://'
    DB_ECHO = True

    engine = sa.create_engine(DB_STRING, echo=DB_ECHO)

    session = sa.orm.scoped_session(sa.orm.sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=engine))
    session.configure(bind=engine)

    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    crud.crud_init(session)


def tearDown():
    print "__init__.py -> tearDown"
    Base.metadata.drop_all()

