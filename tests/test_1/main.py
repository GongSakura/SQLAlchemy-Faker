"""
test_1 is testing fake different types of data
"""

from src.sqlalchemy_faker import SQLFaker
from database import Engine
from schemas import base

base.metadata.drop_all(bind=Engine)
base.metadata.create_all(bind=Engine)

# faker = SQLFaker(metadata=base.metadata,engine=Engine)
metadata = base.metadata
print(metadata.__dict__)

