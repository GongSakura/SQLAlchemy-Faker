from sqlalchemy.orm import declarative_base

from sqlalchemy import Column
from sqlalchemy import String, TEXT, Unicode, UnicodeText
from sqlalchemy import BOOLEAN
from sqlalchemy import DECIMAL, FLOAT, Numeric
from sqlalchemy import INT, SMALLINT, BIGINT

from sqlalchemy import TIMESTAMP, TIME, DATETIME, DATE

base = declarative_base()


class Types(base):
    __tablename__ = 'types'
    int = Column(INT, primary_key=True)
    smallint = Column(SMALLINT)
    bigint = Column(BIGINT)
    float = Column(FLOAT)
    decimal = Column(DECIMAL)
    string = Column(String(20))
    text = Column(TEXT)
    unicode = Column(Unicode(20))
    unicodetext = Column(UnicodeText)

    date = Column(DATE)
    datetime = Column(DATETIME)
    time = Column(TIME)
    timestamp = Column(TIMESTAMP)

# class Types2(base):
#     __tablename__ = 'types2'
#     int = Column(INT, primary_key=True)
#     smallint = Column(SMALLINT)
#     bigint = Column(BIGINT)
#     float = Column(FLOAT)
#     decimal = Column(DECIMAL)
#     string = Column(String(20))
#     text = Column(TEXT)
#     unicode = Column(Unicode(20))
#     unicodetext = Column(UnicodeText)
#
#     date = Column(DATE)
#     datetime = Column(DATETIME)
#     time = Column(TIME)
#     timestamp = Column(TIMESTAMP)
#
# class Types3(base):
#     __tablename__ = 'types3'
#     int = Column(INT, primary_key=True)
#     smallint = Column(SMALLINT)
#     bigint = Column(BIGINT)
#     float = Column(FLOAT)
#     decimal = Column(DECIMAL)
#     string = Column(String(20))
#     text = Column(TEXT)
#     unicode = Column(Unicode(20))
#     unicodetext = Column(UnicodeText)
#
#     date = Column(DATE)
#     datetime = Column(DATETIME)
#     time = Column(TIME)
#     timestamp = Column(TIMESTAMP)
#
#
# class Types4(base):
#     __tablename__ = 'types4'
#     int = Column(INT, primary_key=True)
#     smallint = Column(SMALLINT)
#     bigint = Column(BIGINT)
#     float = Column(FLOAT)
#     decimal = Column(DECIMAL)
#     string = Column(String(20))
#     text = Column(TEXT)
#     unicode = Column(Unicode(20))
#     unicodetext = Column(UnicodeText)
#
#     date = Column(DATE)
#     datetime = Column(DATETIME)
#     time = Column(TIME)
#     timestamp = Column(TIMESTAMP)
#
# class Types5(base):
#     __tablename__ = 'types5'
#     int = Column(INT, primary_key=True)
#     smallint = Column(SMALLINT)
#     bigint = Column(BIGINT)
#     float = Column(FLOAT)
#     decimal = Column(DECIMAL)
#     string = Column(String(20))
#     text = Column(TEXT)
#     unicode = Column(Unicode(20))
#     unicodetext = Column(UnicodeText)
#
#     date = Column(DATE)
#     datetime = Column(DATETIME)
#     time = Column(TIME)
#     timestamp = Column(TIMESTAMP)