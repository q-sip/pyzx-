from dotenv import load_dotenv
import os
import pyzx as zx
from pyzx.graph.zxdb.zxdb import ZXdb
from pyzx.graph.graph_memgraph import GraphMemgraph
from pyzx.utils import EdgeType, VertexType
from tests.tests_from_zxdb._base_unittest_memgraph import MemgraphUnitTestCase

class TestFullReduce(MemgraphUnitTestCase):
    def test_full_reduce(self):
        load_dotenv()
        URI = os.getenv("MEMGRAPH_URI")
        AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))
        g = GraphMemgraph()
        vertices_data = [
        {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 0},
        {"ty": VertexType.X, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 1},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 2},
        {"ty": VertexType.Z, "qubit": 0, "row": 2, 'phsae': 2},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 1},
        {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 4},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.SIMPLE),
            ((1, 3), EdgeType.SIMPLE),
            ((3, 4), EdgeType.HADAMARD),
            ((3, 5), EdgeType.SIMPLE),
            ((5, 6), EdgeType.SIMPLE),
            ((6, 7), EdgeType.SIMPLE),
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[7])
        g_original = g.copy(backend='simple')
        zxdb = ZXdb(uri=URI, user=AUTH[0], password=AUTH[1])
        zxdb.full_reduce()
        g.normalize()
        g_local = g.copy(backend='simple')

        self.assertTrue(zx.compare_tensors(g_local, g_original))