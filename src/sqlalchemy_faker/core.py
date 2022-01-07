"""
The core is construct a tree to store tables structure
Use Breath first search is recommended
"""
from sqlalchemy import Table, MetaData, ForeignKey
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
                referenced_name, _ = self.get_foreign_key(key)
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

    def get_tables(self) -> dict:
        """
        Get tables from the RelationTree via BFS(breath first search)
        :return: a dict e.g {'table_name':table}
        """
        result = defaultdict(Table)
        pending = Queue()
        pending.put(self.root.children)
        while not pending.empty():
            nodes = pending.get()
            for node in nodes.values():
                result[node.name] = node.table
                if len(node.children) != 0:
                    pending.put(node.children)
        return result

    @staticmethod
    def get_table_info(table: Table) -> dict:
        columns = table.columns
        info = defaultdict(dict)
        for c in columns:
            info[c.name] = columns.__dict__

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
    def get_foreign_key(key: ForeignKey) -> tuple:
        name, column = key._get_colspec().split('.')
        return name, column
