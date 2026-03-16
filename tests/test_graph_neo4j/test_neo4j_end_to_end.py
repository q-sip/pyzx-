# tests/test_graph_neo4j/neo4j_end_to_end.py
"""
End-to-End testit neo4j kannalla, verrataan simple-backendiä vastaan
"""
import unittest
from fractions import Fraction

from pyzx.utils import EdgeType, VertexType
from pyzx.graph.graph_s import GraphS

from tests.test_graph_neo4j._base_unittest import Neo4jUnitTestCase





def _sorted_edge_set(graph):
    """Kerätään graafin edget ja pidetään huolta, että järjestys on sama"""
    result = set()
    for e in graph.edges():
        s, t = graph.edge_st(e)
        result.add((min(s, t), max(s, t)))
    return result



class TestGraphCreationE2E(Neo4jUnitTestCase):
    """Testataan, että neo4j sekä Simple-backendien graafit muodostuvat topologisesti oikein."""

    def _make_graphs(self):
        # Neo4j graafin luonti manuaalisesti
        neo4j = self.g
        neo4j.create_graph(
            vertices_data=[
                {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
                {"ty": VertexType.Z, "qubit": 0, "row": 1, "phase": Fraction(1, 2)},
                {"ty": VertexType.X, "qubit": 1, "row": 2, "phase": Fraction(1, 4)},
                {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 3},
            ],
            edges_data=[
                ((0, 1), EdgeType.SIMPLE),
                ((1, 2), EdgeType.HADAMARD),
                ((2, 3), EdgeType.SIMPLE),
            ],
            inputs=[0],
            outputs=[3],
        )

        # Simple graafin luonti manuaalisesti
        simple = GraphS()
        vs = list(simple.add_vertices(4))
        simple.set_type(vs[0], VertexType.BOUNDARY)
        simple.set_qubit(vs[0], 0)
        simple.set_row(vs[0], 0)

        simple.set_type(vs[1], VertexType.Z)
        simple.set_qubit(vs[1], 0)
        simple.set_row(vs[1], 1)
        simple.set_phase(vs[1], Fraction(1, 2))

        simple.set_type(vs[2], VertexType.X)
        simple.set_qubit(vs[2], 1)
        simple.set_row(vs[2], 2)
        simple.set_phase(vs[2], Fraction(1, 4))

        simple.set_type(vs[3], VertexType.BOUNDARY)
        simple.set_qubit(vs[3], 0)
        simple.set_row(vs[3], 3)

        simple.add_edge((0, 1), EdgeType.SIMPLE)
        simple.add_edge((1, 2), EdgeType.HADAMARD)
        simple.add_edge((2, 3), EdgeType.SIMPLE)

        simple.set_inputs((0,))
        simple.set_outputs((3,))

        return neo4j, simple

    def test_vertex_count_matches(self):
        neo4j, simple = self._make_graphs()
        self.assertEqual(neo4j.num_vertices(), simple.num_vertices())

    def test_edge_count_matches(self):
        neo4j, simple = self._make_graphs()
        self.assertEqual(neo4j.num_edges(), simple.num_edges())

    def test_vertex_ids_match(self):
        neo4j, simple = self._make_graphs()
        self.assertEqual(sorted(neo4j.vertices()), sorted(simple.vertices()))

    def test_vertex_types_match(self):
        neo4j, simple = self._make_graphs()
        for v in simple.vertices():
            self.assertEqual(
                neo4j.type(v), simple.type(v),
                f"type mismatch on vertex {v}",
            )

    def test_vertex_phases_match(self):
        neo4j, simple = self._make_graphs()
        for v in simple.vertices():
            self.assertEqual(
                neo4j.phase(v), simple.phase(v),
                f"phase mismatch on vertex {v}",
            )

    def test_vertex_positions_match(self):
        neo4j, simple = self._make_graphs()
        for v in simple.vertices():
            self.assertEqual(
                neo4j.qubit(v), simple.qubit(v),
                f"qubit mismatch on vertex {v}",
            )
            self.assertEqual(
                neo4j.row(v), simple.row(v),
                f"row mismatch on vertex {v}",
            )

    def test_edge_topology_matches(self):
        neo4j, simple = self._make_graphs()
        self.assertEqual(_sorted_edge_set(neo4j), _sorted_edge_set(simple))

    def test_edge_types_match(self):
        neo4j, simple = self._make_graphs()
        for e in simple.edges():
            s, t = simple.edge_st(e)
            self.assertEqual(
                neo4j.edge_type((s, t)), simple.edge_type(e),
                f"edge type mismatch on ({s}, {t})",
            )

    def test_inputs_match(self):
        neo4j, simple = self._make_graphs()
        self.assertEqual(sorted(neo4j.inputs()), sorted(simple.inputs()))

    def test_outputs_match(self):
        neo4j, simple = self._make_graphs()
        self.assertEqual(sorted(neo4j.outputs()), sorted(simple.outputs()))

    def test_depth_matches(self):
        neo4j, simple = self._make_graphs()
        self.assertEqual(neo4j.depth(), simple.depth())





