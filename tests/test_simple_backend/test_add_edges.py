# tests/test_graph_neo4j/test_add_edges.py
import unittest

from pyzx.utils import EdgeType, VertexType

from tests.test_simple_backend._base_unittest import SimpleUnitTestCase


class TestAddEdges(SimpleUnitTestCase):
    def test_add_edges_sets_type_uniformly_and_symmetrically(self):
        g = self.g
        vs = list(g.add_vertices(5))
        self.assertEqual(vs, [0, 1, 2, 3, 4])

        g.add_edges([(0, 1), (1, 2)], EdgeType.SIMPLE)

        self.assertEqual(g.graph[0][1], EdgeType.SIMPLE)
        self.assertEqual(g.graph[1][0], EdgeType.SIMPLE)
        self.assertEqual(g.graph[1][2], EdgeType.SIMPLE)
        self.assertEqual(g.graph[2][1], EdgeType.SIMPLE)

    def test_add_edges_two_calls_can_use_different_uniform_types(self):
        g = self.g
        g.add_vertices(5)

        g.add_edges([(0, 1), (1, 2)], EdgeType.SIMPLE)
        g.add_edges([(2, 3), (3, 4)], EdgeType.HADAMARD)

        # Batch 1 edges
        self.assertEqual(g.graph[0][1], EdgeType.SIMPLE)
        self.assertEqual(g.graph[1][2], EdgeType.SIMPLE)

        # Batch 2 edges
        self.assertEqual(g.graph[2][3], EdgeType.HADAMARD)
        self.assertEqual(g.graph[3][4], EdgeType.HADAMARD)

        # Symmetry
        self.assertEqual(g.graph[3][2], EdgeType.HADAMARD)
        self.assertEqual(g.graph[4][3], EdgeType.HADAMARD)

    def test_add_edges_duplicate_overwrites_type_and_does_not_duplicate(self):
        g = self.g
        g.add_vertices(2)

        g.add_edges([(0, 1)], EdgeType.SIMPLE)
        self.assertEqual(g.graph[0][1], EdgeType.SIMPLE)

        # Re-add same edge with different type
        g.add_edges([(0, 1)], EdgeType.HADAMARD)
        self.assertEqual(g.graph[0][1], EdgeType.HADAMARD)
        self.assertEqual(g.graph[1][0], EdgeType.HADAMARD)

        # Ensure only one adjacency entry exists
        self.assertEqual(list(g.graph[0].keys()), [1])
        self.assertEqual(list(g.graph[1].keys()), [0])
