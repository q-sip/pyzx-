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

class TestAddVerticesE2E(Neo4jUnitTestCase):
    """Tarkistetaan, että vertexit luodaan oikein ja niille annetaan loogiset id:t"""

    def test_add_vertices_returns_consecutive_ids(self):
        neo4j = self.g
        simple = GraphS()

        neo4j_ids = list(neo4j.add_vertices(5))
        simple_ids = list(simple.add_vertices(5))

        self.assertEqual(neo4j_ids, simple_ids)
        self.assertEqual(neo4j.num_vertices(), simple.num_vertices())

    def test_add_vertex_with_properties(self):
        neo4j = self.g
        simple = GraphS()

        nv = neo4j.add_vertex(VertexType.Z, qubit=2, row=3, phase=Fraction(1, 2))
        sv = simple.add_vertex(VertexType.Z, qubit=2, row=3, phase=Fraction(1, 2))

        self.assertEqual(nv, sv)
        self.assertEqual(neo4j.type(nv), simple.type(sv))
        self.assertEqual(neo4j.phase(nv), simple.phase(sv))
        self.assertEqual(neo4j.qubit(nv), simple.qubit(sv))
        self.assertEqual(neo4j.row(nv), simple.row(sv))

class TestEdgeOperationsE2E(Neo4jUnitTestCase):
    """Varmistetaan, että kaikki edgejen operaatiot toimivat loogiseti"""

    def make_base_graphs(self):
        neo4j = self.g
        neo4j.create_graph(
            vertices_data=[
                {"ty": VertexType.Z, "qubit": 0, "row": 0},
                {"ty": VertexType.X, "qubit": 1, "row": 1},
                {"ty": VertexType.Z, "qubit": 2, "row": 2},
            ],
            edges_data=[
                ((0, 1), EdgeType.SIMPLE),
                ((1, 2), EdgeType.HADAMARD),
            ],
        )

        simple = GraphS()
        vs = list(simple.add_vertices(3))
        simple.set_type(vs[0], VertexType.Z)
        simple.set_qubit(vs[0], 0)
        simple.set_row(vs[0], 0)

        simple.set_type(vs[1], VertexType.X)
        simple.set_qubit(vs[1], 1)
        simple.set_row(vs[1], 1)

        simple.set_type(vs[2], VertexType.Z)
        simple.set_qubit(vs[2], 2)
        simple.set_row(vs[2], 2)

        simple.add_edge((0, 1), EdgeType.SIMPLE)
        simple.add_edge((1, 2), EdgeType.HADAMARD)

        return neo4j, simple

    def test_add_edge_increases_count_equally(self):
        neo4j, simple = self.make_base_graphs()

        neo4j.add_edge((0, 2), EdgeType.SIMPLE)
        simple.add_edge((0, 2), EdgeType.SIMPLE)

        self.assertEqual(neo4j.num_edges(), simple.num_edges())

    def test_edge_type_read_back(self):
        neo4j, simple = self.make_base_graphs()

        self.assertEqual(neo4j.edge_type((0, 1)), simple.edge_type((0, 1)))
        self.assertEqual(neo4j.edge_type((1, 2)), simple.edge_type((1, 2)))

    def test_set_edge_type(self):
        neo4j, simple = self.make_base_graphs()

        neo4j.set_edge_type((0, 1), EdgeType.HADAMARD)
        simple.set_edge_type((0, 1), EdgeType.HADAMARD)

        self.assertEqual(neo4j.edge_type((0, 1)), EdgeType.HADAMARD)
        self.assertEqual(neo4j.edge_type((0, 1)), simple.edge_type((0, 1)))

    def test_remove_edges(self):
        neo4j, simple = self.make_base_graphs()

        neo4j.remove_edges([(0, 1)])
        simple.remove_edges([(0, 1)])

        self.assertEqual(neo4j.num_edges(), simple.num_edges())
        self.assertEqual(_sorted_edge_set(neo4j), _sorted_edge_set(simple))


class TestRemoveVerticesE2E(Neo4jUnitTestCase):
    """Varmistetaan, että nodejen poistaminen toimii loogisesti ja samalla tavalla molemmilla backendeillä"""

    def test_remove_middle_vertex(self):
        neo4j = self.g
        neo4j.create_graph(
            vertices_data=[
                {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
                {"ty": VertexType.Z, "qubit": 0, "row": 1},
                {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 2},
            ],
            edges_data=[
                ((0, 1), EdgeType.SIMPLE),
                ((1, 2), EdgeType.SIMPLE),
            ],
            inputs=[0],
            outputs=[2],
        )

        simple = GraphS()
        vs = list(simple.add_vertices(3))
        simple.set_type(vs[0], VertexType.BOUNDARY)
        simple.set_qubit(vs[0], 0)
        simple.set_row(vs[0], 0)

        simple.set_type(vs[1], VertexType.Z)
        simple.set_qubit(vs[1], 0)
        simple.set_row(vs[1], 1)

        simple.set_type(vs[2], VertexType.BOUNDARY)
        simple.set_qubit(vs[2], 0)
        simple.set_row(vs[2], 2)

        simple.add_edge((0, 1), EdgeType.SIMPLE)
        simple.add_edge((1, 2), EdgeType.SIMPLE)
        simple.set_inputs((0,))
        simple.set_outputs((2,))

        neo4j.remove_vertices([1])
        simple.remove_vertices([1])

        self.assertEqual(neo4j.num_vertices(), simple.num_vertices())
        self.assertEqual(sorted(neo4j.vertices()), sorted(simple.vertices()))
        self.assertEqual(neo4j.num_edges(), simple.num_edges())

class TestInputsOutputsE2E(Neo4jUnitTestCase):
    """Varmistetaan inputtien ja outputtien luku ja luominen"""

    def create_graphs(self):
        neo4j = self.g
        neo4j.create_graph(
            vertices_data=[
                {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
                {"ty": VertexType.Z, "qubit": 0, "row": 1},
                {"ty": VertexType.X, "qubit": 1, "row": 1},
                {"ty": VertexType.BOUNDARY, "qubit": 1, "row": 2},
            ],
            edges_data=[
                ((0, 1), EdgeType.SIMPLE),
                ((1, 2), EdgeType.HADAMARD),
                ((2, 3), EdgeType.SIMPLE),
            ],
        )

        simple = GraphS()
        vs = list(simple.add_vertices(4))
        simple.set_type(vs[0], VertexType.BOUNDARY)
        simple.set_qubit(vs[0], 0)
        simple.set_row(vs[0], 0)

        simple.set_type(vs[1], VertexType.Z)
        simple.set_qubit(vs[1], 0)
        simple.set_row(vs[1], 1)

        simple.set_type(vs[2], VertexType.X)
        simple.set_qubit(vs[2], 1)
        simple.set_row(vs[2], 1)

        simple.set_type(vs[3], VertexType.BOUNDARY)
        simple.set_qubit(vs[3], 1)
        simple.set_row(vs[3], 2)

        simple.add_edge((0, 1), EdgeType.SIMPLE)
        simple.add_edge((1, 2), EdgeType.HADAMARD)
        simple.add_edge((2, 3), EdgeType.SIMPLE)

        return neo4j, simple

    def test_set_inputs(self):
        neo4j, simple = self.create_graphs()

        neo4j.set_inputs((0,))
        simple.set_inputs((0,))


        self.assertEqual(sorted(neo4j.inputs()), sorted(simple.inputs()))

    def test_set_outputs(self):
        neo4j, simple = self.create_graphs()

        neo4j.set_outputs((3,))
        simple.set_outputs((3,))

        self.assertEqual(sorted(neo4j.outputs()), sorted(simple.outputs()))

    def test_inputs_outputs_after_create_graph(self):
        neo4j = self.g
        neo4j.create_graph(
            vertices_data=[
                {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
                {"ty": VertexType.Z, "qubit": 0, "row": 1},
                {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 2},
            ],
            edges_data=[
                ((0, 1), EdgeType.SIMPLE),
                ((1, 2), EdgeType.SIMPLE),
            ],
            inputs=[0],
            outputs=[2],
        )

        simple = GraphS()
        vs = list(simple.add_vertices(3))
        simple.set_type(vs[0], VertexType.BOUNDARY)
        simple.set_qubit(vs[0], 0)
        simple.set_row(vs[0], 0)

        simple.set_type(vs[1], VertexType.Z)
        simple.set_qubit(vs[1], 0)
        simple.set_row(vs[1], 1)

        simple.set_type(vs[2], VertexType.BOUNDARY)
        simple.set_qubit(vs[2], 0)
        simple.set_row(vs[2], 2)

        simple.add_edge((0, 1), EdgeType.SIMPLE)
        simple.add_edge((1, 2), EdgeType.SIMPLE)
        simple.set_inputs((0,))
        simple.set_outputs((2,))

        self.assertEqual(sorted(neo4j.inputs()), sorted(simple.inputs()))
        self.assertEqual(sorted(neo4j.outputs()), sorted(simple.outputs()))

class TestVertexPropertiesE2E(Neo4jUnitTestCase):
    """Varmistetaan, että vertexien ominaisuudet luetaan ja asetetaan oikein"""

    def make_graphs(self):
        neo4j = self.g
        neo4j.create_graph(
            vertices_data=[
                {"ty": VertexType.Z, "qubit": 0, "row": 0, "phase": 0},
                {"ty": VertexType.X, "qubit": 1, "row": 1, "phase": 0},
            ],
            edges_data=[((0, 1), EdgeType.SIMPLE)],
        )

        simple = GraphS()
        vs = list(simple.add_vertices(2))
        simple.set_type(vs[0], VertexType.Z)
        simple.set_qubit(vs[0], 0)
        simple.set_row(vs[0], 0)
        simple.set_phase(vs[0], 0)

        simple.set_type(vs[1], VertexType.X)
        simple.set_qubit(vs[1], 1)
        simple.set_row(vs[1], 1)
        simple.set_phase(vs[1], 0)

        simple.add_edge((0, 1), EdgeType.SIMPLE)

        return neo4j, simple

    def test_set_type(self):
        neo4j, simple = self.make_graphs()

        neo4j.set_type(0, VertexType.X)
        simple.set_type(0, VertexType.X)

        self.assertEqual(neo4j.type(0), simple.type(0))
        self.assertEqual(neo4j.type(0), VertexType.X)

    def test_set_phase(self):
        neo4j, simple = self.make_graphs()

        neo4j.set_phase(0, Fraction(3, 4))
        simple.set_phase(0, Fraction(3, 4))

        self.assertEqual(neo4j.phase(0), simple.phase(0))

    def test_set_qubit(self):
        neo4j, simple = self.make_graphs()

        neo4j.set_qubit(0, 5)
        simple.set_qubit(0, 5)

        self.assertEqual(neo4j.qubit(0), simple.qubit(0))

    def test_set_row(self):
        neo4j, simple = self.make_graphs()

        neo4j.set_row(0, 10)
        simple.set_row(0, 10)

        self.assertEqual(neo4j.row(0), simple.row(0))

#class TestEdataVdataE2E(Neo4jUnitTestCase):
