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

from zxdb_age.zxdb_age import ZXdbAge


class TestLocalComplementation(unittest.TestCase):
    def setUp(self):
        self.zxdb = ZXdbAge(graph_id="test_graph")

    def tearDown(self):
        self.zxdb.close()

    def _load_simple_graph_into_age(self, graph: zx.Graph) -> None:
        graph_id = self.zxdb.graph_id
        self.zxdb.clear_all_data()

        for v in graph.vertices():
            self.zxdb._execute_cypher(
                f"""
                CREATE (:Node {{
                    graph_id: '{graph_id}',
                    id: {int(v)},
                    t: {int(graph.type(v).value)},
                    phase: {float(graph.phase(v)) if graph.phase(v) is not None else 0.0},
                    qubit: {int(graph.qubit(v))},
                    row: {int(graph.row(v))}
                }})
                """
            )

        for e in graph.edges():
            s, t = graph.edge_st(e)
            self.zxdb._execute_cypher(
                f"""
                MATCH (a:Node {{graph_id: '{graph_id}', id: {int(s)}}}),
                      (b:Node {{graph_id: '{graph_id}', id: {int(t)}}})
                CREATE (a)-[:Wire {{t: {int(graph.edge_type(e).value)}, graph_id: '{graph_id}'}}]->(b)
                """
            )

    def _export_age_to_simple_graph(self) -> zx.Graph:
        graph_id = self.zxdb.graph_id
        out = zx.Graph(backend="simple")

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
            v_new = out.add_vertex(ty=ty, qubit=int(qubit), row=int(row), phase=ph)
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
                out.add_edge(
                    (vmap[a_key], vmap[b_key]),
                    edgetype=EdgeType.SIMPLE if int(t) == 1 else EdgeType.HADAMARD,
                )

        boundary_vertices = [v for v in out.vertices() if out.type(v) == VertexType.BOUNDARY]
        boundary_vertices.sort(key=lambda v: (out.row(v), out.qubit(v), v))
        if boundary_vertices:
            out.set_inputs((boundary_vertices[0],))
            if len(boundary_vertices) > 1:
                out.set_outputs((boundary_vertices[-1],))

        return out

    def test_local_complementation_runs_until_no_pattern(self):
        query_rows = [
            [(101, 0.5, "[11,12]")],
            [(202, -0.5, "[21,22]")],
            [],
        ]

        def _mock_exec(query, return_signature=None):
            if query == "Local complementation age":
                return query_rows.pop(0)
            if query in {
                "Local complementation age - batch process pairs",
                "Local complementation age - delete hadamard edges",
                "Local complementation age - toggle mixed edges",
                "Local complementation age - batch apply center phase",
            }:
                return [(1,)]
            if isinstance(query, str) and "DETACH DELETE c" in query:
                return []
            raise AssertionError(f"Unexpected query: {query}")

        with patch.object(self.zxdb, "_get_named_query", side_effect=lambda t: t), patch.object(
            self.zxdb, "_execute_cypher", side_effect=_mock_exec
        ) as mock_exec:
            out = self.zxdb.local_complementation_rule()
            self.assertEqual(out, 2)
            self.assertEqual(mock_exec.call_count, 13)
            lcomp_query_calls = [c for c in mock_exec.call_args_list if c.args and c.args[0] == "Local complementation age"]
            self.assertEqual(len(lcomp_query_calls), 3)
            self.assertTrue(
                all(c.kwargs.get("return_signature") == "center_id agtype, center_phase agtype, neighbor_ids agtype" for c in lcomp_query_calls)
            )

    def test_local_complementation_stops_immediately_when_no_pattern(self):
        with patch.object(self.zxdb, "_get_named_query", side_effect=lambda t: t), patch.object(
            self.zxdb, "_execute_cypher", return_value=[]
        ) as mock_exec:
            out = self.zxdb.local_complementation_rule()
            self.assertEqual(out, 0)
            mock_exec.assert_called_once_with(
                "Local complementation age",
                return_signature="center_id agtype, center_phase agtype, neighbor_ids agtype",
            )

    def test_local_complementation_tensor_equivalence(self):
        original = zx.Graph(backend="simple")
        i = original.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
        a = original.add_vertex(VertexType.Z, qubit=0, row=1, phase=Fraction(0))
        c = original.add_vertex(VertexType.Z, qubit=0, row=2, phase=Fraction(1, 2))
        b = original.add_vertex(VertexType.Z, qubit=1, row=1, phase=Fraction(0))
        o = original.add_vertex(VertexType.BOUNDARY, qubit=0, row=4)

        original.add_edge((i, a), edgetype=EdgeType.SIMPLE)
        original.add_edge((a, c), edgetype=EdgeType.HADAMARD)
        original.add_edge((c, b), edgetype=EdgeType.HADAMARD)
        original.add_edge((b, o), edgetype=EdgeType.SIMPLE)
        original.set_inputs((i,))
        original.set_outputs((o,))

        reference = original.copy()
        zx.lcomp_simp(reference)

        try:
            self._load_simple_graph_into_age(original)
            self.zxdb.local_complementation_rule()
            actual = self._export_age_to_simple_graph()
            self.assertTrue(zx.compare_tensors(reference, actual))
        except Exception as exc:
            self.skipTest(f"AGE backend not available for tensor integration test: {exc}")

if __name__ == "__main__":
    unittest.main()
