# tests/test_graph_neo4j/test_add_edges.py
import unittest

from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase


class TestAddEdges(Neo4jE2ETestCase):
    def test_add_edges_simple_enforces_edge_ids(self):
        """
        Ensures that edges created by add_edges have an id property (r.id) set.
        Also enforces that ids exist for each created edge and are distinct.
        """
        g = self.g

        nodes = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 1, "qubit": 0},
            {"ty": VertexType.X, "row": 1, "qubit": 1},
        ]
        g.create_graph(nodes, [])  # Initialize with 0 edges

        edges_to_add = [(0, 1), (1, 2)]
        g.add_edges(edges_to_add)

        query = """
            MATCH (n:Node {graph_id: $gid})-[r:Wire]->(m:Node {graph_id: $gid})
            RETURN n.id as src, m.id as tgt, r.t as type, r.id as id
            ORDER BY src, tgt
        """
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id).data()

        self.assertEqual(len(result), 2)

        # Check each created edge has a non-null id
        for r in result:
            self.assertIn("id", r)
            self.assertIsNotNone(
                r["id"], msg=f"Edge {r['src']}->{r['tgt']} missing r.id"
            )
            self.assertIsInstance(r["id"], int)

        # ids should be distinct for distinct edges
        ids = [r["id"] for r in result]
        self.assertEqual(len(set(ids)), 2)

        # Verify specific connection and type
        edge_0_1 = next((r for r in result if r["src"] == 0 and r["tgt"] == 1), None)
        self.assertIsNotNone(edge_0_1)
        self.assertEqual(edge_0_1["type"], EdgeType.SIMPLE.value)

    def test_add_edges_with_types_enforces_edge_id(self):
        """
        Ensures that the typed edge created by add_edges has an id property.
        """
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
                RETURN r.t as t, r.id as id
                """,
                gid=g.graph_id,
            ).single()

        self.assertIsNotNone(res)
        self.assertEqual(res["t"], EdgeType.HADAMARD.value)

        # Enforce edge id exists
        self.assertIn("id", res)
        self.assertIsNotNone(res["id"], msg="Edge 1->2 missing r.id")
        self.assertIsInstance(res["id"], int)

    def test_add_edges_duplicates_are_merged_and_id_is_stable(self):
        """
        Enforces two things:
          1) duplicates do not create multiple relationships
          2) the relationship has an id, and it does not change when re-adding
        """
        g = self.g
        g.create_graph([{"ty": VertexType.BOUNDARY}, {"ty": VertexType.BOUNDARY}], [])

        # First add
        g.add_edges([(0, 1)])

        with g._get_session() as session:
            first = session.run(
                """
                MATCH (n {graph_id: $gid, id: 0})-[r:Wire]->(m {graph_id: $gid, id: 1})
                RETURN count(r) as c, collect(r.id) as ids
                """,
                gid=g.graph_id,
            ).single()

        self.assertIsNotNone(first)
        self.assertEqual(first["c"], 1)
        self.assertEqual(len(first["ids"]), 1)
        self.assertIsNotNone(
            first["ids"][0], msg="Edge 0->1 missing r.id after first add"
        )
        self.assertIsInstance(first["ids"][0], int)
        first_id = first["ids"][0]

        # Add the same edge again (should not create a new relationship or change id)
        g.add_edges([(0, 1)])

        with g._get_session() as session:
            second = session.run(
                """
                MATCH (n {graph_id: $gid, id: 0})-[r:Wire]->(m {graph_id: $gid, id: 1})
                RETURN count(r) as c, collect(r.id) as ids
                """,
                gid=g.graph_id,
            ).single()

        self.assertIsNotNone(second)
        self.assertEqual(second["c"], 1)
        self.assertEqual(len(second["ids"]), 1)
        self.assertEqual(
            second["ids"][0], first_id, msg="Edge id changed after re-adding duplicate"
        )
