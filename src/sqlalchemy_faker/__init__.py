import warnings

from sqlalchemy import MetaData, String, BLOB, INTEGER, Text, FLOAT, BOOLEAN, insert, text, Integer
from sqlalchemy.future.engine import Engine
from collections import defaultdict
from faker import Faker
import random

from .core import RelationTree

Faker.seed(0)


class SQLFaker:
    def __init__(self, metadata: MetaData, engine: Engine, locale: list = ['en_US']):
        self.metadata = metadata
        self.engine = engine

        self.relationTree = RelationTree(self.metadata)
        self.tables = self.relationTree.get_tables()
        self.faker = Faker(locale)

    def fake(self, name: str, n: int = 10, ) -> None:
        """
        generate fake data
        :param name: table name
        :param n: the number of fake data
        :param locale: a list of localization, it can generate different language fake data
        """
        table = self.tables.get(name, None)

        if table is not None:
            count = 0
            columns_info = self.get_columns_info(table.columns)

            data = []
            while count < n:
                record = {}
                for k, v in columns_info.items():
                    if len(v['foreign_keys']) != 0 and len(v['foreign_key_set']) == 0:
                        raise ValueError(f'Table:{table}, the column {k} failed foreign key constraint')

                    if not v['primary_key'] and not v['unique']:
                        if v.get('foreign_key_set'):
                            record[k] = v.get('foreign_key_set').pop()
                            v.get('foreign_key_set').add(record[k])
                        else:
                            record[k] = self.fake_by_type(v['type'])
                    elif v['primary_key']:
                        if v.get('foreign_key_set'):
                            if len(v.get('foreign_key_set')) == 0:
                                raise ValueError(f'Table:{table}, the column {k} foreign keys had been used up')

                            tmp = v.get('foreign_key_set').pop()
                            v['primary_key_set'].add(tmp)
                            record[k] = tmp
                        else:
                            tmp = self.fake_by_type(v['type'])
                            while tmp in v['primary_key_set']:
                                tmp = self.fake_by_type(v['type'])

                            v['primary_key_set'].add(tmp)
                            record[k] = tmp
                    else:
                        if v.get('foreign_key_set'):
                            if len(v.get('foreign_key_set')) == 0:
                                raise ValueError(f'Table:{table}, the column {k} foreign keys had been used up')

                            tmp = v.get('foreign_key_set').pop()
                            v['key_set'].add(tmp)
                            record[k] = tmp
                        else:
                            tmp = self.fake_by_type(v['type'])
                            while tmp in v['key_set']:
                                tmp = self.fake_by_type(v['type'])
                            v['key_set'].add(tmp)
                            record[k] = tmp

                # insert 100 record each time
                if len(data) == 500:
                    with self.engine.begin() as conn:
                        conn.execute(insert(table).prefix_with('IGNORE'), data)
                    data = []
                else:
                    data.append(record)

                count += 1

            if len(data) != 0:
                with self.engine.begin() as conn:
                    conn.execute(insert(table).prefix_with('IG`NORE'), data)
        else:
            raise ValueError(f'{name} table is not existed')

    def auto_fake(self, n: int = 10):
        """
        auto fake n records
        :param n: the number of fake data
        """
        for name, table in self.tables.items():
            self.fake(name, n)

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
                return self.faker.text(max_nb_chars=10)[:5]
            else:
                return self.faker.text(max_nb_chars=length)

        if isinstance(_type, INTEGER) or isinstance(_type, Integer):
            return self.faker.random_int(step=1)

        if isinstance(_type, FLOAT):
            return self.faker.pyfloat(right_digits=4)

        if isinstance(_type, BOOLEAN):
            return self.faker.pybool()

        if isinstance(_type, BLOB):
            return self.faker.text(max_nb_chars=20).encode('uft-8')
