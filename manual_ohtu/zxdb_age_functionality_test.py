"""Manual smoke test for ZXdbAge methods

Run from project root:
	python manual_ohtu/zxdb_age_functionality_test.py

This script expects a reachable PostgreSQL+AGE instance via env vars
(`DB_URI_POSTGRES` or DB_HOST/DB_PORT/POSTGRES_DB/POSTGRES_USER/POSTGRES_PASSWORD).
"""

from __future__ import annotations

import os
import sys
import uuid


#REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#if REPO_ROOT not in sys.path:
#	sys.path.insert(0, REPO_ROOT)

from pyzx.graph.zxdb_age.zxdb_age import ZXdbAge


def run_to_gh_manual_test() -> bool:
	graph_id = f"manual_to_gh_{uuid.uuid4().hex}"
	db = ZXdbAge(graph_id=graph_id)

	try:
		db.clear_all_data()
		db._execute_cypher(
			"""
			CREATE (:Node {t: 2}), (:Node {t: 2}), (:Node {t: 1})
			"""
		)

		reds_before = db._execute_cypher(
			"MATCH (n:Node) WHERE n.t = 2 RETURN n LIMIT 10",
			return_signature="n agtype",
		)

		db.to_gh()

		reds_after = db._execute_cypher(
			"MATCH (n:Node) WHERE n.t = 2 RETURN n LIMIT 10",
			return_signature="n agtype",
		)

		greens_after = db._execute_cypher(
			"MATCH (n:Node) WHERE n.t = 1 RETURN n LIMIT 10",
			return_signature="n agtype",
		)

		print(f"Graph ID: {graph_id}")
		print(f"Red nodes before to_gh: {len(reds_before)}")
		print(f"Red nodes after to_gh:  {len(reds_after)}")
		print(f"Green nodes after to_gh:{len(greens_after)}")

		passed = len(reds_before) >= 2 and len(reds_after) == 0
		print("PASS" if passed else "FAIL")
		return passed

	except Exception as exc:
		print(f"ERROR: {type(exc).__name__}: {exc}")
		return False
	finally:
		try:
			with db.conn.cursor() as cur:
				cur.execute("SELECT drop_graph(%s, %s);", (graph_id, True))
			db.conn.commit()
		except Exception:
			pass
		db.close()


if __name__ == "__main__":
	ok = run_to_gh_manual_test()
	raise SystemExit(0 if ok else 1)

