import warnings
import random

from datetime import datetime, timedelta

from sqlalchemy import MetaData, insert, text
from sqlalchemy import String, TEXT, Unicode, UnicodeText
from sqlalchemy import BOOLEAN
from sqlalchemy import DECIMAL, FLOAT, Numeric
from sqlalchemy import INT, SMALLINT, BIGINT
from sqlalchemy import JSON
from sqlalchemy import TIMESTAMP, TIME, DATETIME, DATE
from sqlalchemy import BINARY, VARBINARY

from sqlalchemy.future.engine import Engine
from sqlalchemy.orm import Session
from collections import defaultdict
from faker import Faker
from .core import RelationTree
from concurrent.futures import ThreadPoolExecutor
import multiprocessing



class SQLFaker:
    # generator configuration
    TEXT_LENGTH = 50
    INITIAL_DATE = datetime(year=1970, month=1, day=1).date()
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, metadata: MetaData, engine: Engine, locale: list = ['en_US']):

        self.metadata = metadata
        self.engine = engine
        self.relationTree = RelationTree(self.metadata)
        self.tables = self.relationTree.get_tables()
        self.faker = Faker(locale)
        self.provider_name = {'id': [],
                              'address': [self.faker.address],
                              'city': [self.faker.city],
                              'country': [self.faker.country]}
        self.pool = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()+1)

    def fake(self, name: str, n: int = 10, insert_n: int = 100, fake_by: str = 'type') -> None:
        """
        generate fake data
        :param name: table name
        :param n: the number of fake data
        :param insert_n: the number of record inserted to the database each time
        :param fake_by : The way of generating fake data. values can be
            Currently only support fake via data type and column name, if it generate through column name,
            it will use word2vec model to find the most similar data field
        """
        Faker.seed(random.randint(0, 100))
        table = self.tables.get(name, None)
        try:
            if table is not None:
                count = 0
                columns_info = self.get_columns_info(table.columns)

                data = []
                while count < n:
                    record = {}

                    for col_name, col in columns_info.items():

                        if len(col['foreign_keys']) != 0 and len(col['foreign_key_set']) == 0:
                            raise ValueError(f'Table:{table}, the column {col_name} failed foreign key constraint')

                        if not col['primary_key'] and not col['unique']:
                            if col.get('foreign_key_set'):
                                record[col_name] = col.get('foreign_key_set').pop()
                                col.get('foreign_key_set').add(record[col_name])
                            else:

                                record[col_name] = self.generate_by_type(col['type'])
                        elif col['primary_key']:
                            # primary key
                            if col.get('foreign_key_set'):
                                if len(col.get('foreign_key_set')) == 0:
                                    raise ValueError(
                                        f'Table:{table}, the column {col_name} foreign keys had been used up')
                                tmp = col.get('foreign_key_set').pop()
                                col['primary_key_set'].add(tmp)
                                record[col_name] = tmp
                            else:
                                tmp = self.generate_by_type(col['type'], True, count+1)
                                col['primary_key_set'].add(tmp)
                                record[col_name] = tmp
                        else:
                            # unique data
                            if col.get('foreign_key_set'):
                                if len(col.get('foreign_key_set')) == 0:
                                    raise ValueError(
                                        f'Table:{table}, the column {col_name} foreign keys had been used up')

                                tmp = col.get('foreign_key_set').pop()
                                col['key_set'].add(tmp)
                                record[col_name] = tmp
                            else:
                                tmp = self.generate_by_type(col['type'], True, count+1)
                                col['key_set'].add(tmp)
                                record[col_name] = tmp

                    data.append(record)
                    count += 1

                # end loop, insert data
                if len(data) != 0:
                    with Session(self.engine,autoflush=True) as conn:

                        for i in range(int(n / insert_n), 0, -1):
                            conn.execute(insert(table), data[-insert_n:])
                            del data[-insert_n:]
                            conn.commit()

                        if len(data) != 0:
                            conn.execute(insert(table), data)
                            del data

                        conn.commit()



            else:
                raise ValueError(f'{name} table is not existed')
            del columns_info
        except Exception as e:
            warnings.warn(str(e))

    def auto_fake(self, n: int = 10, insert_n: int = 100, fake_by: str = 'type'):
        """
        auto fake n records
        :param insert_n: the number of record inserted to database each time
        :param n: the number of fake data
        :param fake_by : The way of generating fake data. values can be
            Currently only support fake via data type and column name, if it generate through column name,
            it will use word2vec model to find the most similar data field
        """
        for name, table in self.tables.items():
            self.fake(name, n, insert_n)

    def get_columns_info(self, columns) -> dict:
        info = defaultdict(dict)
        for c in columns:
            info[c.name] = c.__dict__
            if info[c.name]['primary_key']:
                info[c.name]['primary_key_set'] = set()

            if len(info[c.name]['foreign_keys']) != 0:

                # as there is only one foreign key for each column
                for key in info[c.name]['foreign_keys']:
                    referenced_table, referenced_column = self.relationTree.get_foreign_key(key)
                    with self.engine.connect() as conn:
                        result = conn.execute(text(f'select {referenced_column} from {referenced_table}'))
                        result = set(result.scalars().all())

                info[c.name]['foreign_key_set'] = result

            if info[c.name]['unique']:
                info[c.name]['key_set'] = set()
        return info

    def generate_by_type(self, _type, is_unique=False, k=0):
        """
        generate fake data by type
        :param k:
        :param is_unique:
        :param _type: Please refer to sqlalchemy sqltypes
        :return: corresponding data
        """

        if is_unique and k < -1 and not isinstance(k, int):
            raise ValueError('If "is_unique"==True, k must be a positive integer')

        if isinstance(_type, TEXT) or isinstance(_type, UnicodeText):
            return self.faker.text(50)

        elif isinstance(_type, String) or isinstance(_type, Unicode):
            length = _type.length
            return self.faker.pystr(min_chars=1, max_chars=length)
        elif isinstance(_type, BIGINT):
            if is_unique:
                return k
            return random.randint(-2 ** 63, 2 ** 63 - 1)
        elif isinstance(_type, SMALLINT):
            if is_unique:
                return k
            return random.randint(-2 ** 15, 2 ** 15 - 1)
        elif isinstance(_type, INT):
            if is_unique:
                return k
            return random.randint(-2 ** 31, 2 ** 31 - 1)

        elif isinstance(_type, DECIMAL):
            if is_unique:
                return self.faker.pydecimal(left_digits=0, positive=True) + k
            return self.faker.pydecimal(left_digits=2,positive=True)
        elif isinstance(_type, FLOAT) or isinstance(_type, Numeric):

            if _type.asdecimal:
                tmp = self.faker.pydecimal(left_digits=0,positive=True)
            else:
                tmp = self.faker.pyfloat(right_digits=_type.precision, positive=True)

            if is_unique:
                tmp += k

            return tmp
        elif isinstance(_type, BOOLEAN):
            if is_unique:
                raise ValueError('Does not support unique value for BOOLEAN type')
            return self.faker.pybool()

        elif isinstance(_type, DATE):
            if is_unique:
                return self.INITIAL_DATE + timedelta(days=k)
            return self.faker.date_time().date()

        elif isinstance(_type, DATETIME):
            if is_unique:
                return datetime.now()
            return self.faker.date_time()

        elif isinstance(_type, TIME):
            if is_unique:
                return datetime.now().time()
            return self.faker.time()

        elif isinstance(_type, TIMESTAMP):
            if is_unique:
                return datetime.now()
            return datetime.now()

        elif isinstance(_type, JSON):
            if is_unique:
                raise ValueError('Does not support unique value for JSON type')
            return self.faker.json()

        elif isinstance(_type, BINARY) or isinstance(_type, VARBINARY):
            length = _type.length
            if is_unique:
                raise ValueError('Does not support unique value for BINARY type')
            return self.faker.binary(length=length)

        raise ValueError(f'Does not support {_type.__repr__()} type')

    def generate_by_name(self, _type, _name, is_unique=False, k=0):
        """
        :param _type: the type of the data
        :param _name: the name of the data, it should be the column name
        :return:
        """
        # TODO: fake by name
        pass

    def insert(self, table, data):
        with Session(self.engine,autoflush=True) as conn:
            conn.execute(insert(table),data)
            conn.commit()
        return True
    #
    # def generate_records(self,table,columns_info,n,start):
    #     records = []
    #     count = 1
    #     while count <= n:
    #         record={}
    #         for col_name, col in columns_info.items():
    #
    #             if len(col['foreign_keys']) != 0 and len(col['foreign_key_set']) == 0:
    #                 raise ValueError(f'Table:{table}, the column {col_name} failed foreign key constraint')
    #
    #             if not col['primary_key'] and not col['unique']:
    #                 if col.get('foreign_key_set'):
    #                     record[col_name] = col.get('foreign_key_set').pop()
    #                     col.get('foreign_key_set').add(record[col_name])
    #                 else:
    #
    #                     record[col_name] = self.generate_by_type(col['type'])
    #             elif col['primary_key']:
    #                 # primary key
    #                 if col.get('foreign_key_set'):
    #                     if len(col.get('foreign_key_set')) == 0:
    #                         raise ValueError(
    #                             f'Table:{table}, the column {col_name} foreign keys had been used up')
    #                     tmp = col.get('foreign_key_set').pop()
    #                     col['primary_key_set'].add(tmp)
    #                     record[col_name] = tmp
    #                 else:
    #                     tmp = self.generate_by_type(col['type'], True, count+start)
    #                     col['primary_key_set'].add(tmp)
    #                     record[col_name] = tmp
    #             else:
    #                 # unique data
    #                 if col.get('foreign_key_set'):
    #                     if len(col.get('foreign_key_set')) == 0:
    #                         raise ValueError(
    #                             f'Table:{table}, the column {col_name} foreign keys had been used up')
    #
    #                     tmp = col.get('foreign_key_set').pop()
    #                     col['key_set'].add(tmp)
    #                     record[col_name] = tmp
    #                 else:
    #                     tmp = self.generate_by_type(col['type'], True, count+start)
    #                     col['key_set'].add(tmp)
    #                     record[col_name] = tmp
    #         count +=1
    #         records.append(record)
    #     # print(len(records))
    #     return records
    #
    # def fake_test(self,table,columns_info,n,start):
    #     data = self.generate_records(table,columns_info,n,start)
    #     self.insert(table,data)
