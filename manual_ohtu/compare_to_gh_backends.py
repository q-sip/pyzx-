"""Manual cross-backend to_gh comparison.

Run from project root:
	python manual_ohtu/compare_to_gh_backends.py

Compares to_gh behavior across:
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


def build_single_red_spider() -> zx.Graph:
	"""Single red spider (X) with simple edges - to_gh should convert to green."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	x = g.add_vertex(VertexType.X, qubit=0, row=1, phase=Fraction(1, 4))  # Red spider
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=2)

	g.add_edge((i, x), edgetype=EdgeType.SIMPLE)
	g.add_edge((x, o), edgetype=EdgeType.SIMPLE)

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def build_red_with_hadamard() -> zx.Graph:
	"""Red spider with hadamard edges - should toggle wires."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	x = g.add_vertex(VertexType.X, qubit=0, row=1, phase=Fraction(1, 3))  # Red
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=2)

	g.add_edge((i, x), edgetype=EdgeType.HADAMARD)  # Will toggle to simple
	g.add_edge((x, o), edgetype=EdgeType.HADAMARD)  # Will toggle to simple

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def build_red_with_mixed_edges() -> zx.Graph:
	"""Red spider with both simple and hadamard edges."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	z_left = g.add_vertex(VertexType.Z, qubit=0, row=1)  # Green
	x = g.add_vertex(VertexType.X, qubit=0, row=2, phase=Fraction(1, 2))  # Red
	z_right = g.add_vertex(VertexType.Z, qubit=1, row=2)  # Green
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=3)

	g.add_edge((i, z_left), edgetype=EdgeType.SIMPLE)
	g.add_edge((z_left, x), edgetype=EdgeType.HADAMARD)
	g.add_edge((x, z_right), edgetype=EdgeType.SIMPLE)
	g.add_edge((z_right, o), edgetype=EdgeType.SIMPLE)

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def build_multiple_red_spiders() -> zx.Graph:
	"""Multiple red spiders in a circuit."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	x1 = g.add_vertex(VertexType.X, qubit=0, row=1, phase=Fraction(1, 6))
	z = g.add_vertex(VertexType.Z, qubit=0, row=2)
	x2 = g.add_vertex(VertexType.X, qubit=0, row=3, phase=Fraction(1, 3))
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=4)

	g.add_edge((i, x1), edgetype=EdgeType.SIMPLE)
	g.add_edge((x1, z), edgetype=EdgeType.SIMPLE)
	g.add_edge((z, x2), edgetype=EdgeType.SIMPLE)
	g.add_edge((x2, o), edgetype=EdgeType.SIMPLE)

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def build_red_all_hadamards() -> zx.Graph:
	"""Red spider connected only by hadamard edges."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	x = g.add_vertex(VertexType.X, qubit=0, row=1, phase=Fraction(1, 4))
	o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=2)

	g.add_edge((i, x), edgetype=EdgeType.HADAMARD)
	g.add_edge((x, o), edgetype=EdgeType.HADAMARD)

	g.set_inputs((i,))
	g.set_outputs((o,))
	return g


def build_no_red_spiders() -> zx.Graph:
	"""No red spiders - to_gh should do nothing."""
	g = zx.Graph(backend="simple")

	i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
	z1 = g.add_vertex(VertexType.Z, qubit=0, row=1, phase=Fraction(1, 2))
	z2 = g.add_vertex(VertexType.Z, qubit=0, row=2, phase=Fraction(1, 4))
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
	"""Export AGE graph back to SimpleGraph for comparison."""
	g = zx.Graph(backend="simple")

	with db.conn.cursor() as cur:
		# Get all nodes - query properties directly
		cur.execute(f"""
			SELECT * FROM ag_catalog.cypher('{db.graph_id}', $$
				MATCH (n:Node) RETURN n.id, n.t, n.phase, n.qubit, n.row
			$$) AS (id agtype, t agtype, phase agtype, qubit agtype, row agtype);
		""")
		rows = cur.fetchall()
		node_map = {}
		for (node_id, node_type, node_phase, node_qubit, node_row) in rows:
			# Convert agtype values to Python types
			node_id = int(node_id)
			node_type = int(node_type)
			node_phase = float(node_phase) if node_phase is not None else 0.0
			node_qubit = int(node_qubit) if node_qubit is not None else 0
			node_row = int(node_row) if node_row is not None else 0

			phase = Fraction(node_phase).limit_denominator()

			if node_type == 0:
				vertex_type = VertexType.BOUNDARY
			elif node_type == 1:
				vertex_type = VertexType.Z
			elif node_type == 2:
				vertex_type = VertexType.X
			else:
				vertex_type = VertexType.BOUNDARY

			v = g.add_vertex(vertex_type, qubit=node_qubit, row=node_row, phase=phase)
			node_map[node_id] = v

	with db.conn.cursor() as cur:
		# Get all edges - query properties directly
		cur.execute(f"""
			SELECT * FROM ag_catalog.cypher('{db.graph_id}', $$
				MATCH (a:Node)-[r:Wire]->(b:Node) RETURN a.id, b.id, r.t
			$$) AS (a_id agtype, b_id agtype, edge_type agtype);
		""")
		rows = cur.fetchall()
		for (a_id, b_id, edge_type) in rows:
			a_id = int(a_id)
			b_id = int(b_id)
			edge_type = int(edge_type)

			if a_id in node_map and b_id in node_map:
				if edge_type == 1:
					et = EdgeType.SIMPLE
				else:
					et = EdgeType.HADAMARD
				g.add_edge((node_map[a_id], node_map[b_id]), edgetype=et)

	# Set boundary vertices as inputs/outputs
	boundary_verts = [v for v in g.vertices() if g.type(v) == VertexType.BOUNDARY]
	if boundary_verts:
		g.set_inputs((boundary_verts[0],))
		if len(boundary_verts) > 1:
			g.set_outputs((boundary_verts[-1],))

	return g


def _safe_compare_tensors(name: str, g1: zx.Graph, g2: zx.Graph) -> tuple[bool, str]:
	"""Safely compare tensors, returning (match, reason)."""
	try:
		return zx.compare_tensors(g1, g2), ""
	except Exception as e:
		return False, f"{type(e).__name__}: {e}"


def _graph_diag(name: str, g: zx.Graph) -> None:
	"""Print graph structure diagnostics."""
	print(f"{name}: vertices={len(list(g.vertices()))}, edges={len(list(g.edges()))}, inputs={len(g.inputs())}, outputs={len(g.outputs())}")
	try:
		for idx, i in enumerate(g.inputs()):
			neighbors = list(g.neighbors(i))
			print(f"  input {idx} (v{i}): degree={len(neighbors)}")
		for idx, o in enumerate(g.outputs()):
			neighbors = list(g.neighbors(o))
			print(f"  output {idx} (v{o}): degree={len(neighbors)}")
	except Exception:
		pass


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

	print("Running SimpleGraph reference (zx.to_gh)...")
	simple_after = original.copy()
	zx.to_gh(simple_after)

	graph_id_mem = f"manual_mem_to_gh_{uuid.uuid4().hex}"
	graph_id_age = f"manual_age_to_gh_{uuid.uuid4().hex}"

	g_mem = None
	age_db = None
	try:
		print("Running Memgraph backend...")
		g_mem = load_fixture_to_memgraph(original, graph_id_mem)
		zx.to_gh(g_mem)
		mem_after = g_mem.copy(backend="simple")

		print("Running AGE backend (ZXdbAge.to_gh)...")
		age_db = load_fixture_to_age_zxdb(original, graph_id_age)
		age_db.to_gh()
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
	"""Test to_gh across multiple fixtures."""
	fixtures = [
		("Single red spider", build_single_red_spider),
		("Red spider with hadamards", build_red_with_hadamard),
		("Red with mixed edges", build_red_with_mixed_edges),
		("Multiple red spiders", build_multiple_red_spiders),
		("Red with all hadamards", build_red_all_hadamards),
		("No red spiders (no-op)", build_no_red_spiders),
	]
	
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
