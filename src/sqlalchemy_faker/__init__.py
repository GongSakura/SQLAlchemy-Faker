import uuid
import warnings
import random

from sqlalchemy import MetaData, String, BLOB, INTEGER, Text, FLOAT, BOOLEAN, insert, text, Integer
from sqlalchemy.future.engine import Engine
from collections import defaultdict
from faker import Faker
from gensim.models import Word2Vec
import gensim.downloader

from .core import RelationTree


class SQLFaker:
    def __init__(self, metadata: MetaData, engine: Engine, locale: list = ['en_US']):
        self.metadata = metadata
        self.engine = engine

        self.relationTree = RelationTree(self.metadata)
        self.tables = self.relationTree.get_tables()
        Faker.seed(random.randint(0, 100))
        self.faker = Faker(locale)

    def fake(self, name: str, n: int = 10, insert_n: int = 100) -> None:
        """
        generate fake data
        :param name: table name
        :param n: the number of fake data
        :param insert_n: the number of record inserted to the database each time
        """
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
                                record[col_name] = self.fake_by_type(col['type'])
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
                                tmp = self.fake_unique_by_type(col['type'], count)
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
                                tmp = self.fake_unique_by_type(col['type'], count)
                                col['key_set'].add(tmp)
                                record[col_name] = tmp

                    data.append(record)
                    count += 1

                # end loop, insert data
                if len(data) != 0:
                    with self.engine.connect() as conn:
                        # each time insert 100
                        for i in range(int(n / insert_n), 0, -1):
                            conn.execute(insert(table), data[-insert_n:])
                            conn.commit()
                            del data[-insert_n:]

                        if len(data) != 0:
                            conn.execute(insert(table), data)
                            conn.commit()
                            del data

                del columns_info
            else:
                raise ValueError(f'{name} table is not existed')
        except Exception as e:
            warnings.warn(str(e))

    def auto_fake(self, n: int = 10, insert_n: int = 100):
        """
        auto fake n records
        :param insert_n: the number of record inserted to database each time
        :param n: the number of fake data
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

    def fake_by_type(self, _type):
        if isinstance(_type, String) or isinstance(_type, Text):
            length = _type.length
            if length is None:
                return self.faker.text(max_nb_chars=10)
            elif length <= 5:
                return self.faker.text(max_nb_chars=6)[:length]
            else:
                return self.faker.text(max_nb_chars=length)

        if isinstance(_type, INTEGER) or isinstance(_type, Integer):
            return self.faker.random_int(min=0, step=1, max=9999999)

        if isinstance(_type, FLOAT):
            return self.faker.pyfloat(right_digits=4)

        if isinstance(_type, BOOLEAN):
            return self.faker.pybool()

        if isinstance(_type, BLOB):
            return self.faker.text(max_nb_chars=20).encode('uft-8')

    def fake_by_name(self, _type, _name):
        """
        :param _type: the type of the data
        :param _name: the name of the data, it should be the column name
        :return:
        """
        pass

    def fake_unique_by_type(self, _type, k):
        """
        generate fake unique data through nth
        :param _type:
        :param k: the kth record
        :return:
        """
        if isinstance(_type, INTEGER) or isinstance(_type, Integer):
            return k + 1
        elif isinstance(_type, FLOAT):
            return round(random.random() + k + 1, 4)
        elif isinstance(_type, BLOB):
            return uuid.uuid4().bytes
        elif isinstance(_type, String) or isinstance(_type, Text):
            length = _type.length
            if length is None:
                return f'{k + 1}-{self.faker.text(max_nb_chars=10)}'
            elif length <= 5:
                return self.faker.text(max_nb_chars=6)[:length]
            else:
                return f'{k + 1}-{self.faker.text(max_nb_chars=length)}'[:length]

        return None
