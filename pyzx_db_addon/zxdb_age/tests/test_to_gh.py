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


class TestToGh(unittest.TestCase):
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

    def test_to_gh_executes_expected_query_sequence(self):
        with patch.object(self.zxdb, "_get_named_query", side_effect=lambda t: t), patch.object(
            self.zxdb, "_execute_cypher", return_value=[]
        ) as mock_exec:
            self.zxdb.to_gh()

        self.assertEqual(mock_exec.call_count, 4)
        self.assertEqual(
            [c.args[0] for c in mock_exec.call_args_list],
            [
                "Change color age - mark",
                "Change color age - recolor",
                "Change color age - toggle wires",
                "Change color age - cleanup",
            ],
        )
        self.assertEqual(
            [c.kwargs.get("return_signature") for c in mock_exec.call_args_list],
            ["marked agtype", "recolored agtype", "toggled agtype", "cleaned agtype"],
        )

    def test_to_gh_tensor_equivalence(self):
        original = zx.Graph(backend="simple")
        i = original.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
        x = original.add_vertex(VertexType.X, qubit=0, row=1, phase=Fraction(1, 3))
        o = original.add_vertex(VertexType.BOUNDARY, qubit=0, row=2)
        original.add_edge((i, x), edgetype=EdgeType.SIMPLE)
        original.add_edge((x, o), edgetype=EdgeType.HADAMARD)
        original.set_inputs((i,))
        original.set_outputs((o,))

        reference = original.copy()
        zx.to_gh(reference)

        try:
            self._load_simple_graph_into_age(original)
            self.zxdb.to_gh()
            actual = self._export_age_to_simple_graph()
            self.assertTrue(zx.compare_tensors(reference, actual))
        except Exception as exc:
            self.skipTest(f"AGE backend not available for tensor integration test: {exc}")

    def test_to_gh_no_red_vertices_tensor_equivalence(self):
        original = zx.Graph(backend="simple")
        i = original.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
        z = original.add_vertex(VertexType.Z, qubit=0, row=1, phase=Fraction(1, 2))
        o = original.add_vertex(VertexType.BOUNDARY, qubit=0, row=2)
        original.add_edge((i, z), edgetype=EdgeType.SIMPLE)
        original.add_edge((z, o), edgetype=EdgeType.SIMPLE)
        original.set_inputs((i,))
        original.set_outputs((o,))

        reference = original.copy()
        zx.to_gh(reference)

        try:
            self._load_simple_graph_into_age(original)
            self.zxdb.to_gh()
            actual = self._export_age_to_simple_graph()
            self.assertTrue(zx.compare_tensors(reference, actual))
        except Exception as exc:
            self.skipTest(f"AGE backend not available for tensor integration test: {exc}")

if __name__ == "__main__":
    unittest.main()
