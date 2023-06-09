# -*- coding: utf-8 -*-

import logging

from py2neo import Graph, Node

from ingest_graph_validator.config import Config


class Hydrator:
    """
    Hydrator main class, any hydrators implemented for the graph validator must implement this interface.
    """

    def __init__(self, graph:Graph):
        self._logger = logging.getLogger(__name__)
        self._graph = graph

        self._nodes = {}
        """Node dictionary. Keys are node ids, and values are py4neo Node objects."""

        self._edges = []
        """Edge list of py4neo Relationship objects."""

        self.batch_size = Config['NEO4J_IMPORT_BATCH_SIZE']

    def hydrate(self):
        """
        This method is called to populate the database. It will use the data contained
        in the _nodes and _edges attributes.
        """

        self.fill_nodes(self._graph, self._nodes)
        self.fill_edges(self._graph, self._edges)

        self._logger.info("hydration finished")

    def fill_nodes(self, graph, nodes):
        tx = self._graph.begin()

        self._logger.info('filling nodes')
        node: Node
        for i, node in enumerate(nodes.values()):
            tx = self.maybe_commit_tx(i, tx)
            tx.create(node)
        tx.commit()

    def maybe_commit_tx(self, i, tx):
        if i % self.batch_size == 0:
            self._logger.info(f'maybe_commit_tx: completed {i} items')
            tx.commit()
            tx = self._graph.begin()
        return tx

    def fill_edges(self, graph, edges):
        tx = self._graph.begin()
        self._logger.info('filling edges')
        for i, edge in enumerate(edges):
            tx = self.maybe_commit_tx(i, tx)
            tx.create(edge)

        tx.commit()
