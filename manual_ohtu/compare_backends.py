"""Manual cross-backend spider-fusion comparison.

Run from project root:
	python manual_ohtu/compare_backends.py

Compares spider fusion behavior across:
- SimpleGraph (PyZX reference)
- Memgraph backend
- AGE rewrite runner (ZXdbAge)
"""

from __future__ import annotations

import os
import sys
import uuid
from fractions import Fraction

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
import pyzx as zx
from pyzx.utils import VertexType, EdgeType
from pyzx.graph.graph_memgraph import GraphMemgraph
from pyzx.graph.zxdb_age.zxdb_age import ZXdbAge

load_dotenv()


def build_simple_fixture() -> zx.Graph:
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	z1 = g.add_vertex(VertexType.Z, qubit=0, row=1, phase=Fraction(1, 2))
	z2 = g.add_vertex(VertexType.Z, qubit=0, row=2, phase=Fraction(1, 2))
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=3)

	g.add_edge((i, z1), edgetype=EdgeType.SIMPLE)
	g.add_edge((z1, z2), edgetype=EdgeType.SIMPLE)
	g.add_edge((z2, o), edgetype=EdgeType.SIMPLE)

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def load_fixture_to_memgraph(g_ref: zx.Graph, graph_id: str) -> GraphMemgraph:
	g_mem = GraphMemgraph(graph_id=graph_id)
	g_mem.remove_all_data()

	vmap = {}
	for v in g_ref.vertices():
		v_new = g_mem.add_vertex(
			ty=g_ref.type(v),
			qubit=g_ref.qubit(v),
			row=g_ref.row(v),
			phase=g_ref.phase(v),
		)
		vmap[v] = v_new

	for e in g_ref.edges():
		s, t = g_ref.edge_st(e)
		g_mem.add_edge((vmap[s], vmap[t]), edgetype=g_ref.edge_type(e))

	g_mem.set_inputs(tuple(vmap[v] for v in g_ref.inputs()))
	g_mem.set_outputs(tuple(vmap[v] for v in g_ref.outputs()))
	return g_mem


def load_fixture_to_age_zxdb(g_ref: zx.Graph, graph_id: str) -> ZXdbAge:
	db = ZXdbAge(graph_id=graph_id)
	db.clear_all_data()

	for v in g_ref.vertices():
		t = int(g_ref.type(v).value)
		phase = float(g_ref.phase(v)) if g_ref.phase(v) is not None else 0.0
		qubit = int(g_ref.qubit(v))
		row = int(g_ref.row(v))
		db._execute_cypher(
			f"""
			CREATE (:Node {{
				graph_id: '{graph_id}',
				id: {int(v)},
				t: {t},
				phase: {phase},
				qubit: {qubit},
				row: {row}
			}})
			"""
		)

	for e in g_ref.edges():
		s, t = g_ref.edge_st(e)
		et = int(g_ref.edge_type(e).value)
		db._execute_cypher(
			f"""
			MATCH (a:Node {{graph_id: '{graph_id}', id: {int(s)}}}),
				  (b:Node {{graph_id: '{graph_id}', id: {int(t)}}})
			CREATE (a)-[:Wire {{t: {et}, graph_id: '{graph_id}'}}]->(b)
			"""
		)

	return db


def age_zxdb_to_simple_graph(db: ZXdbAge) -> zx.Graph:
	g = zx.Graph(backend="simple")

	rows = db._execute_cypher(
		f"""
		MATCH (n:Node)
		WHERE coalesce(n.graph_id, '{db.graph_id}') = '{db.graph_id}'
		RETURN id(n) AS dbid,
			   coalesce(n.id, -1) AS nid,
			   coalesce(n.t, 0) AS t,
			   coalesce(n.phase, 0.0) AS phase,
			   coalesce(n.qubit, -1) AS qubit,
			   coalesce(n.row, -1) AS row
		ORDER BY nid
		""",
		return_signature="dbid agtype, nid agtype, t agtype, phase agtype, qubit agtype, row agtype",
	)

	vmap = {}
	for dbid, _nid, t, phase, qubit, row in rows:
		ty = VertexType(int(t))
		ph = Fraction(float(phase)).limit_denominator() if ty != VertexType.BOUNDARY else None
		v_new = g.add_vertex(ty=ty, qubit=int(qubit), row=int(row), phase=ph)
		vmap[int(dbid)] = v_new

	edge_rows = db._execute_cypher(
		f"""
		MATCH (a:Node)-[w:Wire]->(b:Node)
		WHERE coalesce(a.graph_id, '{db.graph_id}') = '{db.graph_id}'
		  AND coalesce(b.graph_id, '{db.graph_id}') = '{db.graph_id}'
		RETURN id(a) AS a_id, id(b) AS b_id, coalesce(w.t, 1) AS t
		""",
		return_signature="a_id agtype, b_id agtype, t agtype",
	)

	seen = set()
	for a_id, b_id, t in edge_rows:
		u = vmap[int(a_id)]
		v = vmap[int(b_id)]
		key = tuple(sorted((u, v)))
		if key in seen or u == v:
			continue
		seen.add(key)
		et = EdgeType.HADAMARD if int(t) == 2 else EdgeType.SIMPLE
		g.add_edge((u, v), edgetype=et)

	boundaries = [v for v in g.vertices() if g.type(v) == VertexType.BOUNDARY]
	if boundaries:
		boundaries = sorted(boundaries, key=lambda x: (g.row(x), g.qubit(x), x))
		g.set_inputs((boundaries[0],))
		g.set_outputs((boundaries[-1],))

	return g


def _safe_compare_tensors(name: str, g1: zx.Graph, g2: zx.Graph) -> tuple[bool, str]:
	try:
		return zx.compare_tensors(g1, g2, preserve_scalar=False), "ok"
	except Exception as exc:
		return False, f"{type(exc).__name__}: {exc}"


def _graph_diag(name: str, g: zx.Graph) -> None:
	try:
		inputs = list(g.inputs())
	except Exception:
		inputs = []
	try:
		outputs = list(g.outputs())
	except Exception:
		outputs = []

	print(f"{name}: vertices={g.num_vertices()}, edges={g.num_edges()}, inputs={len(inputs)}, outputs={len(outputs)}")
	for v in inputs:
		print(f"  input {v} degree={g.vertex_degree(v)}")
	for v in outputs:
		print(f"  output {v} degree={g.vertex_degree(v)}")


def main() -> int:
	print("Building fixture...")
	original = build_simple_fixture()

	print("Running SimpleGraph reference (zx.spider_simp)...")
	simple_after = original.copy()
	zx.spider_simp(simple_after)

	graph_id_mem = f"manual_mem_spider_{uuid.uuid4().hex}"
	graph_id_age = f"manual_age_spider_{uuid.uuid4().hex}"

	g_mem = None
	age_db = None
	try:
		print("Running Memgraph backend...")
		g_mem = load_fixture_to_memgraph(original, graph_id_mem)
		zx.spider_simp(g_mem)
		mem_after = g_mem.copy(backend="simple")

		print("Running AGE backend (ZXdbAge.spider_fusion)...")
		age_db = load_fixture_to_age_zxdb(original, graph_id_age)
		age_db.spider_fusion()
		age_after = age_zxdb_to_simple_graph(age_db)

		print("Comparing tensors...")
		simple_ok, simple_msg = _safe_compare_tensors("original_vs_simple", original, simple_after)
		mem_ok, mem_msg = _safe_compare_tensors("original_vs_mem", original, mem_after)
		age_ok, age_msg = _safe_compare_tensors("original_vs_age", original, age_after)
		mem_vs_simple, mem_vs_simple_msg = _safe_compare_tensors("mem_vs_simple", mem_after, simple_after)
		age_vs_simple, age_vs_simple_msg = _safe_compare_tensors("age_vs_simple", age_after, simple_after)
		age_vs_mem, age_vs_mem_msg = _safe_compare_tensors("age_vs_mem", age_after, mem_after)

		print(f"original vs simple_after: {simple_ok}")
		print(f"original vs mem_after:    {mem_ok}")
		print(f"original vs age_after:    {age_ok}")
		print(f"mem_after vs simple:      {mem_vs_simple}")
		print(f"age_after vs simple:      {age_vs_simple}")
		print(f"age_after vs mem:         {age_vs_mem}")
		if not simple_ok:
			print(f"  reason original vs simple_after: {simple_msg}")
		if not mem_ok:
			print(f"  reason original vs mem_after: {mem_msg}")
		if not age_ok:
			print(f"  reason original vs age_after: {age_msg}")
		if not mem_vs_simple:
			print(f"  reason mem_after vs simple: {mem_vs_simple_msg}")
		if not age_vs_simple:
			print(f"  reason age_after vs simple: {age_vs_simple_msg}")
		if not age_vs_mem:
			print(f"  reason age_after vs mem: {age_vs_mem_msg}")

		if not all([simple_ok, mem_ok, age_ok, mem_vs_simple, age_vs_simple, age_vs_mem]):
			print("\nGraph diagnostics:")
			_graph_diag("original", original)
			_graph_diag("simple_after", simple_after)
			_graph_diag("mem_after", mem_after)
			_graph_diag("age_after", age_after)

		all_ok = all([simple_ok, mem_ok, age_ok, mem_vs_simple, age_vs_simple, age_vs_mem])
		print("PASS" if all_ok else "FAIL")
		return 0 if all_ok else 1
	except Exception as exc:
		print(f"ERROR: {type(exc).__name__}: {exc}")
		return 1
	finally:
		if g_mem is not None:
			try:
				g_mem.remove_all_data()
			except Exception:
				pass
			try:
				g_mem.close()
			except Exception:
				pass

		if age_db is not None:
			try:
				with age_db.conn.cursor() as cur:
					cur.execute("SELECT drop_graph(%s, %s);", (graph_id_age, True))
				age_db.conn.commit()
			except Exception:
				pass
			try:
				age_db.close()
			except Exception:
				pass


if __name__ == "__main__":
	raise SystemExit(main())

