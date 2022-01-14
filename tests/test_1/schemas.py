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
