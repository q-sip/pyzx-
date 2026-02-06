import unittest
from pyzx.utils import VertexType
from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase

class TestRow(Neo4jE2ETestCase):
    def test_row_returns_correct_value(self):
        """
        Ensures that row correctly gets an already existing value.
        """
        g = self.g
        # Initialize with a known row value
        g.create_graph([{"ty": VertexType.Z, "row": 4.5}], [])
        
        val = g.row(0)
        self.assertEqual(val, 4.5)

    def test_row_returns_minus_one_if_property_missing(self):
        """
        Ensures that querying a node without a row property returns -1.
        """
        g = self.g
        g.create_graph([{"ty": VertexType.X}], [])
        
        # Force remove the property to be certain
        with g._get_session() as session:
            session.run("MATCH (n {graph_id: $gid, id: 0}) REMOVE n.row", gid=g.graph_id)

        val = g.row(0)
        self.assertEqual(val, -1)

    def test_row_on_nonexistent_vertex_returns_minus_one(self):
        """
        If the vertex id doesn't exist in the graph, it should return -1
        """
        # Graph is empty
        val = self.g.row(999)
        self.assertEqual(val, -1)