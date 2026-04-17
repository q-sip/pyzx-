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
import time
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


def test_fixture(
	graph_num: int,
	g_ref: zx.Graph,
	methods: list[str],
	compare_tensors: bool,
) -> tuple[bool, dict[str, dict[str, float]]]:
	"""Test a single fixture across all backends and methods.
	
	Args:
		graph_num: Graph number for display
		g_ref: Reference graph (SimpleGraph)
		methods: List of methods to test ['spider_fusion', 'to_gh', 'local_complementation']
		compare_tensors: Whether to export backend graphs and compare tensors
	
	Returns:
		Tuple of:
		- True if all tested steps succeed (and comparisons pass when enabled), False otherwise
		- Nested dict: {method: {backend: time_in_seconds}}
	"""
	print(f"\nGraph #{graph_num}: vertices={g_ref.num_vertices()}, edges={g_ref.num_edges()}")
	
	timings: dict[str, dict[str, float]] = {method: {} for method in methods}
	results = {method: {} for method in methods}
	
	graph_id_mem = f"manual_mem_{uuid.uuid4().hex[:8]}"
	graph_id_age = f"manual_age_{uuid.uuid4().hex[:8]}"
	
	g_mem = None
	age_db = None
	all_ok = True
	
	try:
		for method in methods:
			print(f"  {method}:", end="")
			
			# SimpleGraph
			simple_after = g_ref.copy()
			t0 = time.perf_counter()
			if method == "spider_fusion":
				zx.spider_simp(simple_after)
			elif method == "to_gh":
				zx.to_gh(simple_after)
			elif method == "local_complementation":
				zx.lcomp_simp(simple_after)
			timings[method]["simple"] = time.perf_counter() - t0
			
			# Memgraph
			g_mem = load_fixture_to_memgraph(g_ref, graph_id_mem)
			t0 = time.perf_counter()
			if method == "spider_fusion":
				zx.spider_simp(g_mem)
			elif method == "to_gh":
				zx.to_gh(g_mem)
			elif method == "local_complementation":
				zx.lcomp_simp(g_mem)
			timings[method]["memgraph"] = time.perf_counter() - t0
			mem_after = g_mem.copy(backend="simple") if compare_tensors else None
			g_mem.remove_all_data()
			g_mem.close()
			g_mem = None
			
			# AGE - use specific method calls
			age_db = load_fixture_to_age_zxdb(g_ref, graph_id_age)
			t0 = time.perf_counter()
			try:
				if method == "spider_fusion":
					age_db.spider_fusion()
				elif method == "to_gh":
					age_db.to_gh()
				elif method == "local_complementation":
					age_db.local_complementation_rule()
				timings[method]["age"] = time.perf_counter() - t0
			except (NotImplementedError, AttributeError) as e:
				# If method not implemented on AGE, skip it
				timings[method]["age"] = 0.0
				print(f" SKIP(not impl)", end="")
				try:
					with age_db.conn.cursor() as cur:
						cur.execute("SELECT drop_graph(%s, %s);", (graph_id_age, True))
					age_db.conn.commit()
				except Exception:
					pass
				age_db.close()
				age_db = None
				continue
			
			age_after = age_zxdb_to_simple_graph(age_db) if compare_tensors else None
			try:
				with age_db.conn.cursor() as cur:
					cur.execute("SELECT drop_graph(%s, %s);", (graph_id_age, True))
				age_db.conn.commit()
			except Exception:
				pass
			age_db.close()
			age_db = None
			
			# Compare results (optional)
			if compare_tensors:
				mem_vs_simple, _ = _safe_compare_tensors("mem_vs_simple", mem_after, simple_after)
				try:
					age_vs_simple, _ = _safe_compare_tensors("age_vs_simple", age_after, simple_after)
				except Exception:
					age_vs_simple = False

				method_ok = mem_vs_simple and age_vs_simple
				results[method] = {"mem_vs_simple": mem_vs_simple, "age_vs_simple": age_vs_simple}
			else:
				method_ok = True
				results[method] = {"speed_only": True}
			
			status = "PASS" if method_ok else "FAIL"
			print(f" {status}", end="")
			all_ok = all_ok and method_ok
		
		print()
		return all_ok, timings
		
	except Exception as exc:
		print(f" ERROR: {type(exc).__name__}: {exc}")
		return False, timings
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
	"""Test rewrite methods across multiple fixtures and backends."""
	parser = argparse.ArgumentParser(description="Compare rewrite methods across SimpleGraph, Memgraph and AGE")
	parser.add_argument(
		"--graphs",
		type=int,
		default=5,
		help="Number of random graphs to generate and test (default: 5)"
	)
	parser.add_argument(
		"--nodes",
		type=int,
		default=12,
		help="Internal node count per random fixture (default: 12)"
	)
	parser.add_argument(
		"--edge-prob",
		type=float,
		default=0.18,
		help="Extra edge probability for random fixture (default: 0.18)"
	)
	parser.add_argument(
		"--seed",
		type=int,
		default=42,
		help="Random seed for reproducibility (default: 42)"
	)
	parser.add_argument(
		"--method",
		type=str,
		choices=["spider_fusion", "to_gh", "local_complementation", "all"],
		default="all",
		help="Which method(s) to test (default: all)"
	)
	parser.add_argument(
		"--with-tensor-compare",
		action="store_true",
		help="Enable tensor comparison across backends (disabled by default for speed and memory safety)",
	)
	args = parser.parse_args()
	compare_tensors = args.with_tensor_compare
	
	# Determine which methods to test
	if args.method == "all":
		methods = ["spider_fusion", "to_gh", "local_complementation"]
	else:
		methods = [args.method]
	
	print(f"Testing {args.graphs} random graphs with methods: {', '.join(methods)}")
	print(f"Graph parameters: nodes={args.nodes}, edge_prob={args.edge_prob}, seed={args.seed}")
	print(f"Tensor comparison: {'enabled' if compare_tensors else 'disabled (speed-only)'}")
	print()
	
	results = {}
	timing_results: dict[int, dict[str, dict[str, float]]] = {}
	
	for graph_num in range(1, args.graphs + 1):
		# Generate a unique seed for each graph
		graph_seed = args.seed + graph_num
		
		# Build random fixture
		g_ref = build_random_big_fixture(
			nodes=args.nodes,
			extra_edge_prob=args.edge_prob,
			seed=graph_seed
		)
		
		# Test across backends and methods
		try:
			passed, timings = test_fixture(graph_num, g_ref, methods, compare_tensors)
			results[graph_num] = passed
			timing_results[graph_num] = timings
		except Exception as e:
			print(f"  EXCEPTION: {type(e).__name__}: {e}")
			results[graph_num] = False
			timing_results[graph_num] = {}
	
	# Summary
	print(f"\n{'='*70}")
	print("SUMMARY")
	print(f"{'='*70}")
	
	total = len(results)
	passed = sum(1 for p in results.values() if p)
	print(f"Passed: {passed}/{total}\n")
	
	# Timing summary
	print(f"{'='*70}")
	print("SPEED SUMMARY (seconds)")
	print(f"{'='*70}")
	print(f"{'Method':<20} {'Simple':>12} {'Memgraph':>12} {'AGE':>12}")
	
	method_times: dict[str, list[float]] = {m: {"simple": [], "memgraph": [], "age": []} for m in methods}
	
	for graph_num in sorted(timing_results.keys()):
		timings = timing_results[graph_num]
		for method in methods:
			if method in timings:
				for backend in ["simple", "memgraph", "age"]:
					if backend in timings[method]:
						method_times[method][backend].append(timings[method][backend])
	
	# Print averages per method
	for method in methods:
		times = method_times[method]
		s_avg = sum(times["simple"]) / len(times["simple"]) if times["simple"] else 0.0
		m_avg = sum(times["memgraph"]) / len(times["memgraph"]) if times["memgraph"] else 0.0
		a_avg = sum(times["age"]) / len(times["age"]) if times["age"] else 0.0
		print(
			f"{method:<20} "
			f"{(f'{s_avg:.6f}' if s_avg > 0 else '-'):>12} "
			f"{(f'{m_avg:.6f}' if m_avg > 0 else '-'):>12} "
			f"{(f'{a_avg:.6f}' if a_avg > 0 else '-'):>12}"
		)
	
	return 0 if all(results.values()) else 1


if __name__ == "__main__":
	raise SystemExit(main())

