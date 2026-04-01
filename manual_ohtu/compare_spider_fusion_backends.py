"""Manual cross-backend spider-fusion comparison.

Run from project root:
	python manual_ohtu/compare_spider_fusion_backends.py

Compares spider fusion behavior across:
- SimpleGraph (PyZX reference)
- Memgraph backend
- AGE rewrite runner (ZXdbAge)
"""

from __future__ import annotations

import argparse
import os
import random
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
	"""Two Z-spiders connected by simple edge."""
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


def build_x_spider_fixture() -> zx.Graph:
	"""Two X-spiders connected by simple edge."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	x1 = g.add_vertex(VertexType.X, qubit=0, row=1, phase=Fraction(1, 4))
	x2 = g.add_vertex(VertexType.X, qubit=0, row=2, phase=Fraction(1, 4))
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=3)

	g.add_edge((i, x1), edgetype=EdgeType.SIMPLE)
	g.add_edge((x1, x2), edgetype=EdgeType.SIMPLE)
	g.add_edge((x2, o), edgetype=EdgeType.SIMPLE)

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def build_three_spider_chain() -> zx.Graph:
	"""Three Z-spiders in chain - all should fuse to one."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	z1 = g.add_vertex(VertexType.Z, qubit=0, row=1, phase=Fraction(1, 6))
	z2 = g.add_vertex(VertexType.Z, qubit=0, row=2, phase=Fraction(1, 3))
	z3 = g.add_vertex(VertexType.Z, qubit=0, row=3, phase=Fraction(1, 2))
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=4)

	g.add_edge((i, z1), edgetype=EdgeType.SIMPLE)
	g.add_edge((z1, z2), edgetype=EdgeType.SIMPLE)
	g.add_edge((z2, z3), edgetype=EdgeType.SIMPLE)
	g.add_edge((z3, o), edgetype=EdgeType.SIMPLE)

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def build_mixed_phases() -> zx.Graph:
	"""Two Z-spiders with different phases to verify phase sum."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	z1 = g.add_vertex(VertexType.Z, qubit=0, row=1, phase=Fraction(1, 3))
	z2 = g.add_vertex(VertexType.Z, qubit=0, row=2, phase=Fraction(1, 6))
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=3)

	g.add_edge((i, z1), edgetype=EdgeType.SIMPLE)
	g.add_edge((z1, z2), edgetype=EdgeType.SIMPLE)
	g.add_edge((z2, o), edgetype=EdgeType.SIMPLE)

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def build_no_fusion_hadamard() -> zx.Graph:
	"""Two Z-spiders connected by hadamard - should NOT fuse."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	z1 = g.add_vertex(VertexType.Z, qubit=0, row=1)
	z2 = g.add_vertex(VertexType.Z, qubit=0, row=2)
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=3)

	g.add_edge((i, z1), edgetype=EdgeType.SIMPLE)
	g.add_edge((z1, z2), edgetype=EdgeType.HADAMARD)  # Hadamard edge - no fusion
	g.add_edge((z2, o), edgetype=EdgeType.SIMPLE)

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def build_red_green_no_fusion() -> zx.Graph:
	"""Red and green spiders - should NOT fuse."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	z = g.add_vertex(VertexType.Z, qubit=0, row=1)  # Green
	x = g.add_vertex(VertexType.X, qubit=0, row=2)  # Red
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=3)

	g.add_edge((i, z), edgetype=EdgeType.SIMPLE)
	g.add_edge((z, x), edgetype=EdgeType.SIMPLE)  # Simple edge with mixed colors
	g.add_edge((x, o), edgetype=EdgeType.SIMPLE)

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def build_random_big_fixture(nodes: int = 30, extra_edge_prob: float = 0.18, seed: int = 1337) -> zx.Graph:
	"""Random larger graph for stress-testing spider fusion across backends."""
	rng = random.Random(seed)
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=nodes + 1)

	phase_choices = [Fraction(0), Fraction(1, 2), Fraction(-1, 2), Fraction(1, 4), Fraction(-1, 4)]
	internal = []
	for row in range(1, nodes + 1):
		vtype = VertexType.Z if rng.random() < 0.55 else VertexType.X
		phase = rng.choice(phase_choices)
		v = g.add_vertex(vtype, qubit=0, row=row, phase=phase)
		internal.append(v)

	chain = [i] + internal + [o]
	for left, right in zip(chain, chain[1:]):
		et = EdgeType.SIMPLE if rng.random() < 0.8 else EdgeType.HADAMARD
		g.add_edge((left, right), edgetype=et)

	for idx in range(len(internal)):
		for jdx in range(idx + 2, len(internal)):
			if rng.random() < extra_edge_prob:
				et = EdgeType.SIMPLE if rng.random() < 0.7 else EdgeType.HADAMARD
				try:
					g.add_edge((internal[idx], internal[jdx]), edgetype=et)
				except Exception:
					pass

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

	def _parse_phase(value) -> Fraction:
		if isinstance(value, (int, float)):
			return Fraction(float(value)).limit_denominator()
		text = str(value).strip().strip('"')
		try:
			return Fraction(text)
		except Exception:
			return Fraction(float(text)).limit_denominator()

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
		ORDER BY coalesce(n.id, -1)
		""",
		return_signature="dbid agtype, nid agtype, t agtype, phase agtype, qubit agtype, row agtype",
	)

	vmap = {}
	for dbid, _nid, t, phase, qubit, row in rows:
		ty = VertexType(int(t))
		ph = _parse_phase(phase) if ty != VertexType.BOUNDARY else None
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

	for a_id, b_id, t in edge_rows:
		u = vmap[int(a_id)]
		v = vmap[int(b_id)]
		et = EdgeType.HADAMARD if int(t) == 2 else EdgeType.SIMPLE
		try:
			g.add_edge((u, v), edgetype=et)
		except Exception:
			# Keep export robust in case AGE has edge patterns that are not reducible in simple backend.
			pass

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


def test_fixture(name: str, builder) -> bool:
	"""Test a single fixture across all backends.
	
	Args:
		name: Test case name
		builder: Callable that returns a fixture graph
	
	Returns:
		True if all backends agree, False otherwise
	"""
	print(f"\n{'='*60}")
	print(f"Test: {name}")
	print(f"{'='*60}")
	
	print("Building fixture...")
	original = builder()

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
		mem_vs_simple, mem_vs_simple_msg = _safe_compare_tensors("mem_vs_simple", mem_after, simple_after)
		age_vs_simple, age_vs_simple_msg = _safe_compare_tensors("age_vs_simple", age_after, simple_after)
		age_vs_mem, age_vs_mem_msg = _safe_compare_tensors("age_vs_mem", age_after, mem_after)

		print(f"mem_after vs simple:      {mem_vs_simple}")
		print(f"age_after vs simple:      {age_vs_simple}")
		print(f"age_after vs mem:         {age_vs_mem}")
		if not mem_vs_simple:
			print(f"  reason mem_after vs simple: {mem_vs_simple_msg}")
		if not age_vs_simple:
			print(f"  reason age_after vs simple: {age_vs_simple_msg}")
		if not age_vs_mem:
			print(f"  reason age_after vs mem: {age_vs_mem_msg}")

		if not all([mem_vs_simple, age_vs_simple, age_vs_mem]):
			print("\nGraph diagnostics:")
			_graph_diag("simple_after", simple_after)
			_graph_diag("mem_after", mem_after)
			_graph_diag("age_after", age_after)

		all_ok = all([mem_vs_simple, age_vs_simple, age_vs_mem])
		print(f"Result: {'PASS' if all_ok else 'FAIL'}")
		return all_ok
	except Exception as exc:
		print(f"ERROR: {type(exc).__name__}: {exc}")
		return False
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


def main() -> int:
	"""Test spider fusion across multiple fixtures."""
	parser = argparse.ArgumentParser(description="Compare spider_fusion across SimpleGraph, Memgraph and AGE")
	parser.add_argument("--random-big", action="store_true", help="Include an additional random large fixture")
	parser.add_argument("--random-nodes", type=int, default=30, help="Internal node count for random fixture")
	parser.add_argument("--random-edge-prob", type=float, default=0.18, help="Extra edge probability for random fixture")
	parser.add_argument("--random-seed", type=int, default=1337, help="Random seed for random fixture")
	args = parser.parse_args()

	fixtures = [
		("Two Z-spiders (same phases)", build_simple_fixture),
		("Two X-spiders (same phases)", build_x_spider_fixture),
		("Three Z-spiders chain", build_three_spider_chain),
		("Two Z-spiders (mixed phases)", build_mixed_phases),
		("Hadamard edge (no fusion)", build_no_fusion_hadamard),
		("Red+Green (no fusion)", build_red_green_no_fusion),
	]

	if args.random_big:
		fixtures.append(
			(
				f"Random big graph (nodes={args.random_nodes}, p={args.random_edge_prob}, seed={args.random_seed})",
				lambda: build_random_big_fixture(
					nodes=args.random_nodes,
					extra_edge_prob=args.random_edge_prob,
					seed=args.random_seed,
				),
			)
		)
	
	results = {}
	for name, builder in fixtures:
		try:
			passed = test_fixture(name, builder)
			results[name] = passed
		except Exception as e:
			print(f"EXCEPTION in {name}: {type(e).__name__}: {e}")
			results[name] = False
	
	print(f"\n\n{'='*60}")
	print("SUMMARY")
	print(f"{'='*60}")
	for name, passed in results.items():
		status = "✓ PASS" if passed else "✗ FAIL"
		print(f"{status}: {name}")
	
	total = len(results)
	passed = sum(1 for p in results.values() if p)
	print(f"\nTotal: {passed}/{total} passed")
	
	return 0 if all(results.values()) else 1


if __name__ == "__main__":
	raise SystemExit(main())

