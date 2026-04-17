import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import psycopg
from dotenv import load_dotenv


load_dotenv()


logging.basicConfig(
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


class ZXdbAge:
    """Skeleton rewrite engine for Apache AGE-backed ZX simplification."""

    def __init__(
        self,
        graph_id: Optional[str] = None,
        query_dir: Optional[str] = None,
    ):
        self.graph_id = graph_id if graph_id is not None else "graph_test_zxdb_age"
        self.basic_rewrite_rule_queries: Dict[str, Dict[str, Any]] = {}
        self._conn: Optional[psycopg.Connection] = None
        self._session_prepared = False
        self._query_dir = Path(query_dir) if query_dir is not None else Path(__file__).parent / "query_collections"

        self._load_default_query_collections()

    @property
    def conn(self) -> psycopg.Connection:
        """Create AGE connection lazily."""
        if self._conn is not None and bool(getattr(self._conn, "closed", False)):
            self._conn = None
            self._session_prepared = False
        if self._conn is None:
            db_uri = os.getenv("DB_URI_POSTGRES")
            if db_uri:
                self._conn = psycopg.connect(db_uri)
            else:
                connect_kwargs = {
                    "host": os.getenv("DB_HOST"),
                    "port": os.getenv("DB_PORT"),
                    "dbname": os.getenv("POSTGRES_DB"),
                    "user": os.getenv("POSTGRES_USER"),
                    "password": os.getenv("POSTGRES_PASSWORD"),
                }
                self._conn = psycopg.connect(**connect_kwargs)
            self._prepare_session()
        return self._conn

    def _prepare_session(self) -> None:
        """Prepare AGE extension and search path once per DB connection."""
        if self._session_prepared:
            return
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS age;")
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute("SELECT 1 FROM ag_catalog.ag_graph WHERE name = %s;", (self.graph_id,))
            if cur.fetchone() is None:
                cur.execute("SELECT create_graph(%s);", (self.graph_id,))
        self.conn.commit()
        self._session_prepared = True

    def close(self) -> None:
        """Explicitly close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            self._session_prepared = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _load_collection_file(self, file_name: str) -> None:
        path = self._query_dir / file_name
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as f:
            query_collection = json.load(f)
        for entry in query_collection.get("items", []):
            title = entry.get("title")
            if title:
                self.basic_rewrite_rule_queries[title] = entry

    def _load_default_query_collections(self) -> None:
        """Load query collection JSON files from query_collections directory."""
        for file_name in (
            "main_queries.json",
            "memgraph-collection-zxdb-age.json",
            "collection-Rewrite-queries-ZXdb-age.json",
            "collection-Labeling-queries-ZXdb-age.json",
            "collection-circuit-extraction-age.json",
            "age-specific-queries.json",
        ):
            self._load_collection_file(file_name)

    def _wrap_cypher(self, cypher_query: str, return_signature: str = "result agtype") -> str:
        """Wrap a raw Cypher query so it can be executed via ag_catalog.cypher."""
        return (
            f"SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$\n"
            f"{cypher_query}\n"
            f"$$) AS ({return_signature});"
        )

    def _execute_cypher(self, cypher_query: str, return_signature: str = "result agtype") -> list:
        """Execute raw Cypher wrapped for AGE and return fetched rows."""
        sql = self._wrap_cypher(cypher_query, return_signature=return_signature)
        max_attempts = int(os.getenv("ZXDB_AGE_MAX_RETRIES", "3"))
        base_sleep = float(os.getenv("ZXDB_AGE_RETRY_BASE_SLEEP", "0.25"))
        max_sleep = float(os.getenv("ZXDB_AGE_RETRY_MAX_SLEEP", "1.5"))
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                with self.conn.cursor() as cur:
                    cur.execute(sql)
                    rows = cur.fetchall() if cur.description else []
                self.conn.commit()
                return rows
            except psycopg.OperationalError as exc:
                last_error = exc
                msg = str(exc).lower()
                transient = (
                    "connection is lost" in msg
                    or "connection is closed" in msg
                    or "recovery mode" in msg
                    or "server closed the connection" in msg
                    or "terminating connection" in msg
                    or "consuming input failed" in msg
                    or "could not receive data from server" in msg
                    or "connection not open" in msg
                )
                try:
                    if self._conn is not None:
                        self._conn.rollback()
                except Exception:
                    pass
                if not transient or attempt == max_attempts:
                    raise
                self.close()
                time.sleep(min(base_sleep * attempt, max_sleep))
            except psycopg.InterfaceError as exc:
                last_error = exc
                msg = str(exc).lower()
                transient = (
                    "connection" in msg
                    or "closed" in msg
                    or "not open" in msg
                )
                try:
                    if self._conn is not None:
                        self._conn.rollback()
                except Exception:
                    pass
                if not transient or attempt == max_attempts:
                    raise
                self.close()
                time.sleep(min(base_sleep * attempt, max_sleep))
            except Exception:
                self.conn.rollback()
                raise

        if last_error is not None:
            raise last_error
        return []

    def _get_named_query(self, title: str) -> str:
        """Get query body from loaded collection by title."""
        entry = self.basic_rewrite_rule_queries.get(title)
        if not entry:
            raise KeyError(f"Query title not found: {title}")
        return str(entry["query"]["code"]["value"])

    def run_named_query(self, title: str, return_signature: str = "result agtype") -> list:
        """Execute a stored query by title."""
        query = self._get_named_query(title)
        return self._execute_cypher(query, return_signature=return_signature)

    def clear_all_data(self) -> None:
        """Delete all nodes in the current AGE graph."""
        self._execute_cypher("MATCH (n) DETACH DELETE n")

    def empty_graphdb(self) -> None:
        """Alias for clear_all_data to mirror zxdb naming."""
        self.clear_all_data()

    def hadamard_cancel(self) -> int:
        """TODO: implement AGE hadamard cancellation rewrite pipeline."""
        return 0

    def remove_identities(self, G) -> int:
        """
        Collapse nodes with:
        - attribute 'phase' even
        - degree == 2
        Replace them by directly connecting their neighbors.
        
        Parameters:
            G (nx.Graph or nx.DiGraph): graph with node attributes
            
        Returns:
            bool: True if any nodes were removed
        """
        nodes_to_remove = []

        nodes = G.vertices

        for node in list(nodes):
            # Check node conditions
            if (
                nodes[node].get("phase") is not None and
                nodes[node]["phase"] % 2 == 0 and
                node.vertex_degree == 2
            ):
                neighbors = list(G.neighbors(node))
                if len(neighbors) != 2:
                    continue  # safety check
                #Fix from here onwards
                v1, v2 = neighbors

                # Avoid creating duplicate edges if already connected
                if not G.has_edge(v1, v2):
                    G.add_edge(v1, v2, type="Wire")

                nodes_to_remove.append(node)

        # Remove nodes after iteration
        for node in nodes_to_remove:
            G.remove_node(node)

        return len(nodes_to_remove) > 0


    def spider_fusion(self) -> int:
        """Apply spider-fusion."""

        total_patterns = 0
        trace = os.getenv("ZXDB_AGE_TRACE_SPIDER", "0").strip().lower() in {"1", "true", "yes", "on"}
        query = self._get_named_query("Spider fusion age")
        reverse_query = self._get_named_query("Spider fusion age reverse")
        normalize_query = self._get_named_query("Spider fusion age - normalize").replace("__GRAPH_ID__", self.graph_id)
        self_loop_query = self._get_named_query("Spider fusion age - self loops").replace("__GRAPH_ID__", self.graph_id)
        cleanup_merged_mark_query = self._get_named_query("Spider fusion age - cleanup merged mark").replace("__GRAPH_ID__", self.graph_id)

        while True:
            if trace:
                print("[spider_fusion] stage=merge")
            try:
                rows = self._execute_cypher(query, return_signature="rewrites_applied agtype")
                merged = int(rows[0][0]) if rows and rows[0] and rows[0][0] is not None else 0
            except psycopg.OperationalError:
                rows = self._execute_cypher(reverse_query, return_signature="rewrites_applied agtype")
                merged = int(rows[0][0]) if rows and rows[0] and rows[0][0] is not None else 0
            if merged == 0:
                rows = self._execute_cypher(reverse_query, return_signature="rewrites_applied agtype")
                merged = int(rows[0][0]) if rows and rows[0] and rows[0][0] is not None else 0
            if merged == 0:
                break
            if trace:
                print(f"[spider_fusion] merged={merged} stage=normalize")
            self._execute_cypher(normalize_query, return_signature="normalized agtype")
            if trace:
                print("[spider_fusion] stage=self_loops")
            self._execute_cypher(self_loop_query, return_signature="loops_deleted agtype")
            if trace:
                print("[spider_fusion] stage=cleanup_mark")
            self._execute_cypher(cleanup_merged_mark_query, return_signature="cleaned agtype")
            total_patterns += merged

        print(f"Spider fusion(age): Processed {total_patterns} patterns.")
        return total_patterns

    def pivot_rule(self) -> int:
        """TODO: implement AGE pivot rewrite."""
        return 0

    def local_complementation_rule(self) -> int:
        """Apply local complementation rewrites until no more patterns are found.
        
        Uses efficient batched queries:
        - Query 1: Find valid center + all neighbors
        - Query 2: Batch MERGE all neighbor pairs (creates Hadamard edges)
        - Query 3: Batch DELETE pure Hadamard pairs
        - Query 4: Batch toggle mixed edges and apply phase
        - Query 5: Apply center phase + delete center
        """
        
        def _parse_neighbor_ids(value: object) -> list[int]:
            if value is None:
                return []
            if isinstance(value, list):
                return [int(v) for v in value]
            if isinstance(value, tuple):
                return [int(v) for v in value]
            text = str(value).strip()
            if not text:
                return []
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [int(v) for v in parsed]
            except Exception:
                pass
            text = text.strip('[]')
            if not text:
                return []
            return [int(part.strip()) for part in text.split(',') if part.strip()]

        def _parse_scalar(value: object) -> float:
            if isinstance(value, (int, float)):
                return float(value)
            text = str(value).strip().strip('"')
            return float(text)

        total_patterns = 0
        while True:
            # Query 1: Find valid center and neighbors
            rows = self._execute_cypher(
                self._get_named_query("Local complementation age"),
                return_signature="center_id agtype, center_phase agtype, neighbor_ids agtype",
            )
            if not rows or not rows[0]:
                break

            center_id = int(rows[0][0])
            center_phase = _parse_scalar(rows[0][1])
            neighbor_ids = sorted(set(_parse_neighbor_ids(rows[0][2])))
            if not neighbor_ids:
                break

            # Build all neighbor pairs
            pairs = []
            for idx, left_id in enumerate(neighbor_ids[:-1]):
                for right_id in neighbor_ids[idx + 1 :]:
                    pairs.append((left_id, right_id))

            # Extract left and right IDs as separate lists for batch queries
            left_ids = [p[0] for p in pairs]
            right_ids = [p[1] for p in pairs]

            if pairs:
                # Query 2: Batch MERGE to create/ensure all Hadamard edges
                query_merge = self._get_named_query(
                    "Local complementation age - batch process pairs"
                )
                query_merge = query_merge.replace("__LEFT_IDS__", str(left_ids))
                query_merge = query_merge.replace("__RIGHT_IDS__", str(right_ids))
                self._execute_cypher(
                    query_merge,
                    return_signature="processed agtype",
                )

                # Query 3: Batch DELETE pure Hadamard edges
                query_delete = self._get_named_query(
                    "Local complementation age - delete hadamard edges"
                )
                query_delete = query_delete.replace("__LEFT_IDS__", str(left_ids))
                query_delete = query_delete.replace("__RIGHT_IDS__", str(right_ids))
                self._execute_cypher(
                    query_delete,
                    return_signature="deleted agtype",
                )

                # Query 4: Batch toggle mixed edges and apply phase
                query_toggle = self._get_named_query(
                    "Local complementation age - toggle mixed edges"
                )
                query_toggle = query_toggle.replace("__LEFT_IDS__", str(left_ids))
                query_toggle = query_toggle.replace("__RIGHT_IDS__", str(right_ids))
                self._execute_cypher(
                    query_toggle,
                    return_signature="toggled agtype",
                )

            # Query 5: Batch apply center phase to all neighbors (single query)
            query_phase = self._get_named_query(
                "Local complementation age - batch apply center phase"
            )
            query_phase = query_phase.replace("__NEIGHBOR_IDS__", str(neighbor_ids))
            query_phase = query_phase.replace("__CENTER_PHASE__", str(center_phase))
            self._execute_cypher(
                query_phase,
                return_signature="updated agtype",
            )

            # Delete center
            self._execute_cypher(
                f"""
                MATCH (c:Node {{graph_id: '{self.graph_id}', id: {center_id}}})
                DETACH DELETE c
                """
            )
            total_patterns += 1

        print(f"Local Complementation")
        return total_patterns

    def phase_gadget_fusion_rule(self) -> int:
        """TODO: implement AGE phase gadget fusion rewrite."""
        return 0

    def pivot_gadget_rule(self) -> int:
        """TODO: implement AGE pivot gadget rewrite."""
        return 0

    def gadget_simp(self) -> int:
        """TODO: implement AGE gadget simplification rewrite."""
        return 0

    def pivot_boundary_rule(self) -> int:
        """TODO: implement AGE boundary pivot rewrite."""
        return 0

    def bialgebra_simp(self) -> int:
        """TODO: implement AGE bialgebra simplification rewrite."""
        return 0

    def get_degree_distribution(self) -> Dict[int, int]:
        """TODO: implement AGE degree-distribution query."""
        return {}

    def turn_hadamard_gates_into_edges(self) -> None:
        """TODO: implement AGE hadamard-node to hadamard-edge conversion."""
        return

    def copy_simp(self) -> int:
        """TODO: implement AGE copy simplification rewrite."""
        return 0

    def to_gh(self) -> None:
        """Change color of all red vertices to green."""
        self._execute_cypher(
            self._get_named_query("Change color age - mark"),
            return_signature="marked agtype",
        )
        self._execute_cypher(
            self._get_named_query("Change color age - recolor"),
            return_signature="recolored agtype",
        )
        self._execute_cypher(
            self._get_named_query("Change color age - toggle wires"),
            return_signature="toggled agtype",
        )
        self._execute_cypher(
            self._get_named_query("Change color age - cleanup"),
            return_signature="cleaned agtype",
        )

    def remove_isolated_vertices(self) -> None:
        """TODO: implement isolated-vertex cleanup."""
        return

    def supplementarity_simp(self) -> int:
        """TODO: implement AGE supplementarity rewrite."""
        return 0

    def interior_clifford_simp(self) -> bool:
        """Skeleton interior Clifford simplification loop mirroring PyZX."""
        changed_any = False
        self.spider_fusion()
        self.to_gh()
        while True:
            i1 = self.remove_identities()
            i2 = self.spider_fusion()
            i3 = self.pivot_rule()
            i4 = self.local_complementation_rule()
            if not (i1 or i2 or i3 or i4):
                break
            changed_any = True
        return changed_any

    def clifford_simp(self) -> bool:
        """Skeleton Clifford simplification loop."""
        changed = False
        while True:
            changed = self.interior_clifford_simp() or changed
            i2 = self.pivot_boundary_rule()
            if not i2:
                break
        return changed

    def full_reduce(self) -> None:
        """Skeleton full-reduction pipeline for AGE backend, mirroring PyZX order."""
        self.interior_clifford_simp()
        self.pivot_gadget_rule()
        while True:
            self.clifford_simp()
            i = self.gadget_simp()
            self.interior_clifford_simp()
            k = self.copy_simp()
            l = self.supplementarity_simp()
            j = self.pivot_gadget_rule()
            if not (i or j or k or l):
                self.remove_isolated_vertices()
                break


ZXdb = ZXdbAge
