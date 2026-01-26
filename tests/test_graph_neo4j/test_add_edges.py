# tests/test_graph_neo4j/test_add_edges.py
import unittest

from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase


class TestAddEdges(Neo4jE2ETestCase):
    def test_add_edges_simple(self):
        g = self.g

        nodes = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 1, "qubit": 0},
            {"ty": VertexType.X, "row": 1, "qubit": 1},
        ]
        g.create_graph(nodes, [])

        edges_to_add = [(0, 1), (1, 2)]
        g.add_edges(edges_to_add)

        query = """
            MATCH (n:Node {graph_id: $gid})-[r:Wire]->(m:Node {graph_id: $gid})
            RETURN n.id as src, m.id as tgt, r.t as type
        """
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id).data()

        self.assertEqual(len(result), 2)

        edge_0_1 = next((r for r in result if r["src"] == 0 and r["tgt"] == 1), None)
        self.assertIsNotNone(edge_0_1)
        self.assertEqual(edge_0_1["type"], EdgeType.SIMPLE.value)

    def test_add_edges_with_types(self):
        g = self.g

        nodes = [
            {"ty": VertexType.BOUNDARY},
            {"ty": VertexType.Z},
            {"ty": VertexType.X},
        ]
        g.create_graph(nodes, [])

        edges = [(0, 1), (1, 2)]
        edge_types = [EdgeType.SIMPLE, EdgeType.HADAMARD]
        g.add_edges(edges, edge_data=edge_types)

        with g._get_session() as session:
            res = session.run(
                """
                MATCH (n {graph_id: $gid, id: 1})-[r:Wire]->(m {graph_id: $gid, id: 2})
                RETURN r.t as t
                """,
                gid=g.graph_id,
            ).single()

        self.assertIsNotNone(res)
        self.assertEqual(res["t"], EdgeType.HADAMARD.value)

    def test_add_edges_duplicates_are_merged(self):
        """
        Current implementation uses MERGE, so adding the same (s,t,type) twice should not
        create duplicates for that relationship pattern.
        """
        g = self.g
        g.create_graph([{"ty": VertexType.BOUNDARY}, {"ty": VertexType.BOUNDARY}], [])

        g.add_edges([(0, 1)])
        g.add_edges([(0, 1)])

        with g._get_session() as session:
            res = session.run(
                """
                MATCH (n {graph_id: $gid, id: 0})-[r:Wire]->(m {graph_id: $gid, id: 1})
                RETURN count(r) as c
                """,
                gid=g.graph_id,
            ).single()

        self.assertIsNotNone(res)
        self.assertEqual(res["c"], 1)
