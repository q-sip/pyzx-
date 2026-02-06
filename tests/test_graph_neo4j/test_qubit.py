from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase, Neo4jUnitTestCase

class TestQubit(Neo4jE2ETestCase):
    def test_qubit_added_to_vertex(self):
        g = self.g

        g.set_qubit(1, 2)
        check_qubit=g.qubit(1)

        self.assertEqual(check_qubit, "2")