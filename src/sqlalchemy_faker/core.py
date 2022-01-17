"""
The core is construct a tree to store tables structure
Use Breath first search is recommended
"""
from sqlalchemy import Table, MetaData, ForeignKey, text
from sqlalchemy.future.engine import Engine
from collections import defaultdict
from queue import Queue


class RelationNode:
    def __init__(self, name: str, table: Table = None, parent=None, layer: int = 0) -> None:
        self.name = name
        self.table = table
        self.parent = parent
        self.children = defaultdict(RelationNode)
        self.layer = layer


class RelationTree:

    def __init__(self, metadata: MetaData) -> None:
        self.root = RelationNode(name='_root')
        self.metadata = metadata
        self.parse_metadata()
        self.insert_tables,self.query_tables = self.get_tables()

    def add_node(self, table: Table) -> None:
        """
        add a relationNode to the tree
        """
        # keep added record
        deepest_layer = 0
        deepest_parent = None

        if len(table.foreign_keys) == 0:
            node = self.search_node(self.root, table.name)
            if node is None:
                self.root.children[table.name] = RelationNode(name=table.name, table=table, parent=self.root, layer=1)
            else:
                node.table = table

        else:
            for key in table.foreign_keys:
                # find the referenced table
                referenced_name, _ = self.parse_foreign_key(key)
                referenced_node = self.search_node(root=self.root, name=referenced_name)

                if referenced_node is None:
                    referenced_node = RelationNode(name=referenced_name)
                    self.root.children[referenced_name] = referenced_node
                    if deepest_layer < referenced_node.layer + 1:
                        self.root.children[referenced_name].children[table.name] = RelationNode(name=table.name,
                                                                                                table=table,
                                                                                                parent=referenced_node,
                                                                                                layer=referenced_node.layer + 1)
                        if deepest_parent:
                            del deepest_parent.children[table.name]

                        deepest_layer = referenced_node.layer + 1
                        deepest_parent = referenced_node
                else:
                    if deepest_layer < referenced_node.layer + 1:
                        referenced_node.children[table.name] = RelationNode(name=table.name,
                                                                            table=table,
                                                                            parent=referenced_node,
                                                                            layer=referenced_node.layer + 1)
                        if deepest_parent:
                            del deepest_parent.children[table.name]

                        deepest_layer = referenced_node.layer + 1
                        deepest_parent = referenced_node

    def parse_metadata(self) -> bool:
        """
        construct a tree from metadata
        :return:
        """
        try:
            tables = self.metadata.tables
            for t in tables.values():
                self.add_node(t)
            return True
        except Exception as e:
            raise e

    def get_tables(self):
        """
        Get tables from the RelationTree via BFS(breath first search)
        :return: a list
        """
        insert_result = []
        query_result = defaultdict(dict)
        pending = Queue()
        pending.put(self.root.children)
        while not pending.empty():
            nodes = pending.get()
            for node in nodes.values():
                insert_result.append([node.name, node.layer])
                query_result[node.name] = {'layer': node.layer, 'table': node.table}
                if len(node.children) != 0:
                    pending.put(node.children)
        return insert_result, query_result

    def get_columns_info(self, name: str, fetch_from_db: bool = False, engine: Engine = None) -> dict:
        columns = self.query_tables[name]['table'].columns
        info = defaultdict(dict)
        for c in columns:
            info[c.name] = c.__dict__
            if info[c.name]['primary_key'] or info[c.name]['unique']:
                info[c.name]['key_set'] = set()

            # as there is only one foreign key for each column
            for key in info[c.name]['foreign_keys']:
                referenced_table, referenced_column = self.parse_foreign_key(key)

                # fetch from database
                if fetch_from_db is True and isinstance(engine, Engine):
                    with engine.connect() as conn:
                        result = conn.execute(text(f'select {referenced_column} from {referenced_table}'))
                        info[c.name]['foreign_key_set'] = set(result.scalars().all())

                else:
                    # fetch from tables
                    info[c.name]['foreign_key_set'] = self.query_tables[referenced_table]['columns_info'][referenced_column][
                        'key_set'].copy()

        return info

    @staticmethod
    def search_node(root, name: str) -> RelationNode:
        if len(root.children) == 0:
            return None
        if name in root.children:
            return root.children.get(name)
        else:
            for child in root.children.values():
                result = RelationTree.search_node(root=child, name=name)
                if result:
                    return result
            return None

    @staticmethod
    def parse_foreign_key(key: ForeignKey) -> tuple:
        name, column = key._get_colspec().split('.')
        return name, column
