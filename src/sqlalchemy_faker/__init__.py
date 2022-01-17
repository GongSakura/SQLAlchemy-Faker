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

from faker import Faker

from .core import RelationTree


class SQLFaker:
    # generator configuration
    TEXT_LENGTH = 50
    INITIAL_DATE = datetime(year=1970, month=1, day=1).date()
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, metadata: MetaData, engine: Engine, locale: list = ['en_US']):

        self.relationTree = RelationTree(metadata)
        self.engine = engine
        self.insert_tables = self.relationTree.insert_tables
        self.query_tables = self.relationTree.query_tables

        self.faker = Faker(locale)
        # self.provider_name = {'id': [],
        #                       'address': [self.faker.address],
        #                       'city': [self.faker.city],
        #                       'country': [self.faker.country]}

    def fake(self, name: str, n: int = 10, insert_n: int = 100, fake_by: str = 'type') -> None:
        """
        generate fake data
        :param name: table name
        :param n: the number of fake data
        :param insert_n: the number of record inserted to the database_1 each time
        :param fake_by : The way of generating fake data. values can be
            Currently only support fake via data type and column name, if it generate through column name,
            it will use word2vec model to find the most similar data field
        """
        table_info = self.query_tables[name]
        try:
            if table_info['table'] is not None:
                count = 0
                data = []

                columns_info = table_info.get('columns_info', None)
                if columns_info is None:
                    columns_info = self.relationTree.get_columns_info(name, True, self.engine)
                    self.query_tables[name]['columns_info'] = columns_info
                    print(f'Table:{name}, Fetch columns_info from database')
                table = table_info['table']
                with Session(self.engine) as conn:

                    while count < n:
                        record = {}
                        for col_name, col in columns_info.items():

                            if len(col['foreign_keys']) != 0 and len(col['foreign_key_set']) == 0:
                                raise ValueError(f'Table:{name}, the column {col_name} failed foreign key constraint')

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
                                            f'Table:{name}, the column {col_name} foreign keys had been used up')
                                    tmp = col.get('foreign_key_set').pop()
                                    col['key_set'].add(tmp)
                                    record[col_name] = tmp
                                else:
                                    tmp = self.generate_by_type(col['type'], True, count + 1)
                                    col['key_set'].add(tmp)
                                    record[col_name] = tmp

                            else:
                                # unique data
                                if col.get('foreign_key_set'):
                                    if len(col.get('foreign_key_set')) == 0:
                                        raise ValueError(
                                            f'Table:{name}, the column {col_name} foreign keys had been used up')

                                    tmp = col.get('foreign_key_set').pop()
                                    col['key_set'].add(tmp)
                                    record[col_name] = tmp
                                else:
                                    tmp = self.generate_by_type(col['type'], True, count + 1)
                                    col['key_set'].add(tmp)
                                    record[col_name] = tmp

                        data.append(record)
                        count += 1

                        if count % insert_n == 0:
                            conn.execute(insert(table).prefix_with("IGNORE"), data)
                            conn.commit()
                            data = []

                    # end loop, insert data
                    if len(data) != 0:
                        conn.execute(insert(table).prefix_with("IGNORE"), data)
                        conn.commit()
                        del data

            else:
                raise ValueError(f'{name} table is not existed')
        except Exception as e:
            warnings.warn(str(e))

    def auto_fake(self, n: int = 10, insert_n: int = 100, fake_by: str = 'type'):
        """
        auto fake n records
        :param insert_n: the number of record inserted to database_1 each time
        :param n: the number of fake data
        :param fake_by : The way of generating fake data. values can be
            Currently only support fake via data type and column name, if it generate through column name,
            it will use word2vec model to find the most similar data field
        """
        pre_layer = 0

        for i in self.insert_tables:
            print(i)
            self.query_tables[i[0]]['columns_info'] = self.relationTree.get_columns_info(i[0])
            cur_layer = i[1]

            self.fake(i[0], n, insert_n)
            print(datetime.now())
            if cur_layer - pre_layer == 2:
                # remove the columns info of tables from pre_player
                for name, info in self.query_tables.items():
                    if info['layer'] == pre_layer:
                        del info['columns_info']
                pre_layer = cur_layer

    def generate_by_type(self, _type, is_unique=False, k=0):
        """
        generate fake data by type
        :param k:
        :param is_unique:
        :param _type: Please refer to sqlalchemy sqltypes
        :return: corresponding data

        Be careful, if string length ==1, it only support 1,114,112 unique character
        """

        if is_unique and k < -1 and not isinstance(k, int):
            raise ValueError('If "is_unique"==True, k must be a positive integer')

        if isinstance(_type, TEXT) or isinstance(_type, UnicodeText):
            if is_unique:
                return chr(k % 255) + '-' + self.faker.text(50)
            return self.faker.text(50)

        elif isinstance(_type, String) or isinstance(_type, Unicode):
            length = _type.length
            if is_unique:
                if length == 1:
                    return chr(k % 255)
                else:
                    return chr(k % 255) + self.faker.unique.pystr(min_chars=1, max_chars=length - 1)
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
            return self.faker.pydecimal(left_digits=2, positive=True)
        elif isinstance(_type, FLOAT) or isinstance(_type, Numeric):

            if _type.asdecimal:
                tmp = self.faker.pydecimal(left_digits=0, positive=True)
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
