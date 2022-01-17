"""
Unit tests
"""

from sqlalchemy import create_engine

from sqlalchemy_utils.functions import database_exists,create_database
from .config import SQL_HOST,SQL_USER,SQL_DATABASE,SQL_PORT,SQL_PASSWORD

# create connection engine
Engine = create_engine(f'mysql+pymysql://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{SQL_DATABASE}')
if not database_exists(Engine.url):
    create_database(Engine.url)

