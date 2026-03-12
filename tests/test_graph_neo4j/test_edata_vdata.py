import unittest
from pyzx.utils import VertexType, EdgeType
from tests.test_graph_neo4j._base_unittest import Neo4jUnitTestCase

class TestVdataEdataE2E(Neo4jUnitTestCase):

    def _setup_standard_graph(self):
        #Luodaan perus graafi testejä varten
        vertices_data = [
            {"ty": VertexType.Z, "qubit": 0, "row": 0},
            {"ty": VertexType.X, "qubit": 1, "row": 1}
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE)
        ]
        self.g.create_graph(vertices_data=vertices_data, edges_data=edges_data)
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
        #Testataan, että kaaren datan poistaminen ei tuhoa kaarta kokonaan
        self._setup_standard_graph()
        g = self.g

        g.set_edata((0,1), "temp", "keep_me")
        g.clear_edata((0,1))

        val = g.edata((0,1), "temp", default="empty")
        self.assertEqual(val, "empty")

        self.assertIn((0,1), g.edges())

    def test_vdata_default_value(self):
        #Testataan, että vdata metodi palauttaa oletusarvon, jos avainta ei ole olemassa
        self._setup_standard_graph()
        g = self.g

        val = g.vdata(0, "non_existent", default="default")
        self.assertEqual(val, "default")
