"""
test_1 is testing fake different types of data
"""

from src.sqlalchemy_faker import SQLFaker
from database import Engine
from schemas import base
from datetime import datetime
base.metadata.drop_all(bind=Engine)
base.metadata.create_all(bind=Engine)

faker = SQLFaker(metadata=base.metadata,engine=Engine)
print(datetime.now())
faker.auto_fake(n=123456,insert_n=500)
print(datetime.now())
# metadata = base.metadata
# print(metadata.__dict__)

