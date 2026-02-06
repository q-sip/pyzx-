from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase, Neo4jUnitTestCase
from pyzx.utils import EdgeType, VertexType

class TestQubit(Neo4jE2ETestCase):
    def test_qubit_added_to_vertex(self):
        g = self.g
        g.create_graph(
            vertices_data=[
                {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
                {"ty": VertexType.Z, "qubit": 0, "row": 1},
                {"ty": VertexType.X, "qubit": 0, "row": 2},
            ],
            edges_data=[
                ((0, 1), EdgeType.SIMPLE)
            ]
        )
        g.set_qubit(1, 2)
        check_qubit=g.qubit(1)

        self.assertEqual(check_qubit, '2')
