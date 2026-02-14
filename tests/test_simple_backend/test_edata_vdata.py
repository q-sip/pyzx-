import unittest
from pyzx.utils import VertexType, EdgeType
from tests.test_simple_backend._base_unittest import SimpleUnitTestCase

class TestVdataEdataE2E(SimpleUnitTestCase):

    def _setup_standard_graph(self):
        g = self.g

        vs = list(g.add_vertices(2))
        self.assertEqual(vs, [0,1])

        #Luodaan perus graafi testejä varten
        vertices_data = [
            {"ty": VertexType.Z, "qubit": 0, "row": 0},
            {"ty": VertexType.X, "qubit": 1, "row": 1}
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE)
        ]

        for v, data in enumerate(vertices_data):
            g.set_type(v, data["ty"])
            g.set_qubit(v, data["qubit"])
            g.set_row(v, data["row"])

        for (s, t), et in edges_data:
            g.add_edge((s, t), et)

        return 0, 1, (0, 1)

    def test_vdata_lifecycle(self):
        #Testataan arvojen asettaminen, hakeminen ja avainten listaaminen metodeilla
        self._setup_standard_graph()
        g = self.g

        g.set_vdata(0, "jordan", 123)
        self.assertEqual(g.vdata(0, "jordan"), 123)

        keys = g.vdata_keys(0)
        self.assertIn("jordan", keys)

    def test_clear_vdata(self):
        #Testataan, että noden datan poistaminen ei tuhoa nodea kokonaan
        self._setup_standard_graph()
        g = self.g

        g.set_vdata(0, "michael", 456)
        g.clear_vdata(0)

        val = g.vdata(0, "michael", default=None)
        self.assertIsNone(val)

        self.assertEqual(g.type(0), VertexType.Z)

    def test_edata_lifecycle(self):
        #Testataan kaaren arvojen asettaminen, hakeminen ja avainten listaaminen metodeilla
        self._setup_standard_graph()
        g = self.g

        g.set_edata((0,1), "weight", 3.14)
        self.assertEqual(g.edata((0,1), "weight"), 3.14)

        keys = g.edata_keys((0,1))

        self.assertTrue(any("weight" in k for k in keys))

    def test_clear_edata(self):
        self._setup_standard_graph()
        g = self.g

        g.set_edata((0, 1), "temp", "keep_me")
        g.clear_edata((0, 1))

        val = g.edata((0, 1), "temp", default="empty")
        self.assertEqual(val, "empty")

        edges = list(g.edges())
        self.assertTrue(((0, 1) in edges) or ((1, 0) in edges), msg=f"edges={edges}")


    def test_vdata_default_value(self):
        #Testataan, että vdata metodi palauttaa oletusarvon, jos avainta ei ole olemassa
        self._setup_standard_graph()
        g = self.g

        val = g.vdata(0, "non_existent", default="default")
        self.assertEqual(val, "default")
