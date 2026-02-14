import unittest
from pyzx.utils import VertexType
from tests.test_graph_neo4j._base_unittest import Neo4jUnitTestCase

class TestSetRow(Neo4jUnitTestCase):
    def test_set_row_persists_value(self):
        """
        Ensures that set_row saves the value to the database.
        """
        g = self.g
        g.create_graph([{"ty": VertexType.Z}], [])

        target_row = 10
        g.set_row(0, target_row)

        # Verify directly via session to ensure the write actually happened
        with g._get_session() as session:
            res = session.run(
                "MATCH (n {graph_id: $gid, id: 0}) RETURN n.row",
                gid=g.graph_id
            ).single()

        self.assertEqual(res["n.row"], target_row)

    def test_set_row_updates_existing_value(self):
        """
        Ensures that calling set_row overwrites a previous value.
        """
        g = self.g
        # Start with row = 1
        g.create_graph([{"ty": VertexType.Z, "row": 1}], [])

        # Change to row = 5
        g.set_row(0, 5)

        self.assertEqual(g.row(0), 5)
