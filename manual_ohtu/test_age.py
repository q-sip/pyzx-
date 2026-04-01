"""Random AGE vs SimpleGraph method comparison harness.

Run from project root:
	python manual_ohtu/test_age.py --method spider_fusion --graphs 5
	python manual_ohtu/test_age.py --method local_complementation --graphs 10 --seed 42
	python manual_ohtu/test_age.py --method all --nodes 8 --extra-edge-prob 0.2
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import uuid
from fractions import Fraction
from typing import Callable, Dict, List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
import pyzx as zx
from pyzx.graph.zxdb_age.zxdb_age import ZXdbAge
from pyzx.utils import EdgeType, VertexType

load_dotenv()


def build_random_graph(nodes: int, extra_edge_prob: float, rng: random.Random) -> zx.Graph:
	"""Build a random ZX graph with boundaries and internal spiders."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=nodes + 1)

	internal: List[int] = []
	phase_choices = [Fraction(0), Fraction(1, 2), Fraction(-1, 2), Fraction(1, 4), Fraction(-1, 4)]

	for row in range(1, nodes + 1):
		vtype = VertexType.Z if rng.random() < 0.5 else VertexType.X
		phase = rng.choice(phase_choices)
		vertex = g.add_vertex(vtype, qubit=0, row=row, phase=phase)
		internal.append(vertex)

	chain = [i] + internal + [o]
	for left, right in zip(chain, chain[1:]):
		edge_type = EdgeType.SIMPLE if rng.random() < 0.75 else EdgeType.HADAMARD
		g.add_edge((left, right), edgetype=edge_type)

	for idx in range(len(internal)):
		for jdx in range(idx + 2, len(internal)):
			if rng.random() < extra_edge_prob:
				edge_type = EdgeType.SIMPLE if rng.random() < 0.6 else EdgeType.HADAMARD
				try:
					g.add_edge((internal[idx], internal[jdx]), edgetype=edge_type)
				except Exception:
					pass

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def load_simple_graph_to_age(g_ref: zx.Graph, graph_id: str) -> ZXdbAge:
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


def export_age_to_simple_graph(db: ZXdbAge) -> zx.Graph:
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

	vmap: Dict[int, int] = {}
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
			pass

	boundaries = [v for v in g.vertices() if g.type(v) == VertexType.BOUNDARY]
	if boundaries:
		boundaries = sorted(boundaries, key=lambda x: (g.row(x), g.qubit(x), x))
		g.set_inputs((boundaries[0],))
		g.set_outputs((boundaries[-1],))

	return g


def _safe_tensor_compare(g1: zx.Graph, g2: zx.Graph) -> Tuple[bool, str]:
	try:
		return zx.compare_tensors(g1, g2, preserve_scalar=False), "ok"
	except Exception as exc:
		return False, f"{type(exc).__name__}: {exc}"


def _graph_vertices_signature(g: zx.Graph) -> List[Tuple[int, int, float | None, int, int]]:
	rows: List[Tuple[int, int, float | None, int, int]] = []
	for v in sorted(g.vertices()):
		phase = float(g.phase(v)) if g.phase(v) is not None else None
		rows.append((int(v), int(g.type(v).value), phase, int(g.qubit(v)), int(g.row(v))))
	return rows


def _graph_edges_signature(g: zx.Graph) -> List[Tuple[int, int, int]]:
	edges: List[Tuple[int, int, int]] = []
	for e in g.edges():
		a, b = g.edge_st(e)
		edges.append((min(int(a), int(b)), max(int(a), int(b)), int(g.edge_type(e).value)))
	return sorted(edges)


def _dump_graph_diff(simple_g: zx.Graph, age_g: zx.Graph) -> str:
	sv = _graph_vertices_signature(simple_g)
	av = _graph_vertices_signature(age_g)
	se = _graph_edges_signature(simple_g)
	ae = _graph_edges_signature(age_g)

	msg: List[str] = []
	msg.append(f"simple counts: vertices={simple_g.num_vertices()}, edges={simple_g.num_edges()}")
	msg.append(f"age counts:    vertices={age_g.num_vertices()}, edges={age_g.num_edges()}")
	
	# Detailed node info
	msg.append("\n=== SIMPLE NODES ===")
	for v in sorted(simple_g.vertices()):
		phase = simple_g.phase(v)
		neighbors = len(list(simple_g.neighbors(v)))
		msg.append(f"  v{v}: type={simple_g.type(v).name}, phase={phase}, qubit={simple_g.qubit(v)}, row={simple_g.row(v)}, neighbors={neighbors}")
	
	msg.append("\n=== AGE NODES ===")
	for v in sorted(age_g.vertices()):
		phase = age_g.phase(v)
		neighbors = len(list(age_g.neighbors(v)))
		msg.append(f"  v{v}: type={age_g.type(v).name}, phase={phase}, qubit={age_g.qubit(v)}, row={age_g.row(v)}, neighbors={neighbors}")
	
	# Detailed edge info
	msg.append("\n=== SIMPLE EDGES ===")
	for e in sorted(simple_g.edges()):
		a, b = simple_g.edge_st(e)
		et = simple_g.edge_type(e).name
		msg.append(f"  e{e}: {a}-{b} ({et})")
	
	msg.append("\n=== AGE EDGES ===")
	for e in sorted(age_g.edges()):
		a, b = age_g.edge_st(e)
		et = age_g.edge_type(e).name
		msg.append(f"  e{e}: {a}-{b} ({et})")
	
	msg.append("\n=== SIGNATURES ===")
	msg.append(f"simple vertices: {sv}")
	msg.append(f"age vertices:    {av}")
	msg.append(f"simple edges: {se}")
	msg.append(f"age edges:    {ae}")
	return "\n".join(msg)


def run_method_compare(
	method_name: str,
	graph: zx.Graph,
	simple_runner: Callable[[zx.Graph], object],
	age_runner: Callable[[ZXdbAge], object],
	dump_on_fail: bool = False,
) -> Tuple[bool, str]:
	graph_id_age = f"manual_age_{method_name}_{uuid.uuid4().hex}"
	age_db: ZXdbAge | None = None

	simple_after = graph.copy()
	simple_runner(simple_after)

	try:
		age_db = load_simple_graph_to_age(graph, graph_id_age)
		age_runner(age_db)
		age_after = export_age_to_simple_graph(age_db)

		same_tensor, reason = _safe_tensor_compare(simple_after, age_after)
		if not same_tensor:
			if dump_on_fail:
				diff = _dump_graph_diff(simple_after, age_after)
				return False, f"tensor mismatch ({reason})\n{diff}"
			return False, f"tensor mismatch ({reason})"
		return True, "match"
	except Exception as exc:
		return False, f"backend error: {type(exc).__name__}: {exc}"
	finally:
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
	parser = argparse.ArgumentParser(description="Random Simple vs AGE rewrite comparison")
	parser.add_argument(
		"--method",
		choices=["spider_fusion", "local_complementation", "all"],
		default="all",
		help="Method to test",
	)
	parser.add_argument("--graphs", type=int, default=5, help="How many random graphs to generate")
	parser.add_argument("--nodes", type=int, default=6, help="Internal spider count per graph")
	parser.add_argument("--extra-edge-prob", type=float, default=0.15, help="Probability of extra internal edges")
	parser.add_argument("--seed", type=int, default=None, help="Optional random seed")
	parser.add_argument("--dump-on-fail", action="store_true", help="Print detailed graph diff when a method comparison fails")
	args = parser.parse_args()

	rng = random.Random(args.seed)

	methods: Dict[str, Tuple[Callable[[zx.Graph], object], Callable[[ZXdbAge], object]]] = {
		"spider_fusion": (lambda g: zx.spider_simp(g), lambda db: db.spider_fusion()),
		"local_complementation": (lambda g: zx.lcomp_simp(g), lambda db: db.local_complementation_rule()),
	}

	selected = list(methods.keys()) if args.method == "all" else [args.method]

	total = 0
	passed = 0
	print(f"Running {args.graphs} random graphs, methods={selected}, seed={args.seed}")

	for graph_index in range(1, args.graphs + 1):
		g = build_random_graph(nodes=args.nodes, extra_edge_prob=args.extra_edge_prob, rng=rng)
		print(f"\nGraph #{graph_index}: vertices={len(list(g.vertices()))}, edges={len(list(g.edges()))}")

		for method_name in selected:
			total += 1
			simple_runner, age_runner = methods[method_name]
			ok, reason = run_method_compare(method_name, g, simple_runner, age_runner, dump_on_fail=args.dump_on_fail)
			if ok:
				passed += 1
				print(f"  [{method_name}] PASS")
			else:
				print(f"  [{method_name}] FAIL: {reason}")

	print("\nSummary")
	print(f"  Passed: {passed}/{total}")
	return 0 if passed == total else 1


if __name__ == "__main__":
	raise SystemExit(main())
