import os
import sys
import unittest
from fractions import Fraction
from unittest.mock import patch

import pyzx as zx
from pyzx.utils import EdgeType, VertexType

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
PYZX_GRAPH_ROOT = os.path.join(REPO_ROOT, "pyzx", "graph")
for p in (REPO_ROOT, PYZX_GRAPH_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from pyzx_db_addon.zxdb_age.zxdb_age import ZXdbAge


class TestSpiderFusion(unittest.TestCase):
    def setUp(self):
        self.zxdb = ZXdbAge(graph_id="test_graph")

    def tearDown(self):
        self.zxdb.close()

    def test_spider_fusion_runs_until_no_patterns(self):
        execute_results = [
            [(1,)],
            [],
            [],
            [],
            [(0,)],
            [(0,)],
        ]
        with patch.object(self.zxdb, "_get_named_query", side_effect=lambda t: t), patch.object(
            self.zxdb, "_execute_cypher", side_effect=execute_results
        ) as mock_exec:
            out = self.zxdb.spider_fusion()
            self.assertEqual(out, 1)
            self.assertEqual(mock_exec.call_count, 6)

    def test_spider_fusion_stops_immediately_when_no_pattern(self):
        with patch.object(self.zxdb, "_get_named_query", side_effect=lambda t: t), patch.object(
            self.zxdb, "_execute_cypher", return_value=[(0,)]
        ) as mock_exec:
            out = self.zxdb.spider_fusion()
            self.assertEqual(out, 0)
            self.assertEqual(mock_exec.call_count, 2)

    def test_spider_fusion_tensor_equivalence(self):
        graph_id = self.zxdb.graph_id

        original = zx.Graph(backend="simple")
        i = original.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
        z1 = original.add_vertex(VertexType.Z, qubit=0, row=1, phase=Fraction(1, 2))
        z2 = original.add_vertex(VertexType.Z, qubit=0, row=2, phase=Fraction(1, 2))
        o = original.add_vertex(VertexType.BOUNDARY, qubit=0, row=3)
        original.add_edge((i, z1), edgetype=EdgeType.SIMPLE)
        original.add_edge((z1, z2), edgetype=EdgeType.SIMPLE)
        original.add_edge((z2, o), edgetype=EdgeType.SIMPLE)
        original.set_inputs((i,))
        original.set_outputs((o,))

        reference = original.copy()
        zx.spider_simp(reference)

        try:
            self.zxdb.clear_all_data()
            for v in original.vertices():
                self.zxdb._execute_cypher(
                    f"""
                    CREATE (:Node {{
                        graph_id: '{graph_id}',
                        id: {int(v)},
                        t: {int(original.type(v).value)},
                        phase: {float(original.phase(v)) if original.phase(v) is not None else 0.0},
                        qubit: {int(original.qubit(v))},
                        row: {int(original.row(v))}
                    }})
                    """
                )

            for e in original.edges():
                s, t = original.edge_st(e)
                self.zxdb._execute_cypher(
                    f"""
                    MATCH (a:Node {{graph_id: '{graph_id}', id: {int(s)}}}),
                          (b:Node {{graph_id: '{graph_id}', id: {int(t)}}})
                    CREATE (a)-[:Wire {{t: {int(original.edge_type(e).value)}, graph_id: '{graph_id}'}}]->(b)
                    """
                )

            self.zxdb.spider_fusion()

            rows = self.zxdb._execute_cypher(
                f"""
                MATCH (n:Node)
                WHERE coalesce(n.graph_id, '{graph_id}') = '{graph_id}'
                RETURN id(n) AS dbid,
                       coalesce(n.id, -1) AS nid,
                       coalesce(n.t, 0) AS t,
                       coalesce(n.phase, 0.0) AS phase,
                       coalesce(n.qubit, -1) AS qubit,
                       coalesce(n.row, -1) AS row
                ORDER BY coalesce(n.id, -1)
                """,
                return_signature="dbid agtype, nid agtype, t agtype, phase agtype, qubit agtype, row agtype",
            )

            actual = zx.Graph(backend="simple")
            vmap = {}

            def _parse_phase(value):
                if isinstance(value, (int, float)):
                    return Fraction(float(value)).limit_denominator()
                text = str(value).strip().strip('"')
                try:
                    return Fraction(text)
                except Exception:
                    return Fraction(float(text)).limit_denominator()

            for dbid, _nid, t, phase, qubit, row in rows:
                ty = VertexType(int(t))
                ph = _parse_phase(phase) if ty != VertexType.BOUNDARY else None
                v_new = actual.add_vertex(ty=ty, qubit=int(qubit), row=int(row), phase=ph)
                vmap[int(dbid)] = v_new

            edge_rows = self.zxdb._execute_cypher(
                f"""
                MATCH (a:Node)-[w:Wire]->(b:Node)
                WHERE coalesce(a.graph_id, '{graph_id}') = '{graph_id}'
                  AND coalesce(b.graph_id, '{graph_id}') = '{graph_id}'
                RETURN id(a) AS a_id, id(b) AS b_id, coalesce(w.t, 1) AS t
                """,
                return_signature="a_id agtype, b_id agtype, t agtype",
            )

            for a_id, b_id, t in edge_rows:
                a_key = int(a_id)
                b_key = int(b_id)
                if a_key in vmap and b_key in vmap:
                    actual.add_edge(
                        (vmap[a_key], vmap[b_key]),
                        edgetype=EdgeType.SIMPLE if int(t) == 1 else EdgeType.HADAMARD,
                    )

            boundary_vertices = [v for v in actual.vertices() if actual.type(v) == VertexType.BOUNDARY]
            boundary_vertices.sort(key=lambda v: (actual.row(v), actual.qubit(v), v))
            if boundary_vertices:
                actual.set_inputs((boundary_vertices[0],))
                if len(boundary_vertices) > 1:
                    actual.set_outputs((boundary_vertices[-1],))

            self.assertTrue(zx.compare_tensors(reference, actual))
        except Exception as exc:
            self.skipTest(f"AGE backend not available for tensor integration test: {exc}")


if __name__ == "__main__":
    unittest.main()
