# tests/test_graph_age/test_add_vertices.py
import os
import unittest
import uuid
import io

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType

stream = io.StringIO()

class TestGraphAGEAddVertices(unittest.TestCase):

    def test_correct_ids(self):
        g = GraphAGE()
        returns = g.add_vertices(3)
        expected =  [0, 1, 2]
        self.assertEqual(expected, returns)
    
    def test_saved_to_database(self):
        g = GraphAGE()
        g.add_vertices(3)
        query = f"""
        SELECT * FROM cypher('{g.graph_id}', $$
        MATCH (n)
        RETURN n.id
        $$) AS (id agtype);
        """
        db_result = g.db_fetch(query)

        expected =  [('0',), ('1',), ('2',)]
        self.assertEqual(expected, db_result)

