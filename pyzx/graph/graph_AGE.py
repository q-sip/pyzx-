"""
Docstring for pyzx.graph.graph_AGE
"""

# pylint: disable=invalid-name,abstract-method,arguments-differ,no-member,super-init-not-called,broad-exception-caught,too-many-public-methods,too-many-lines,too-many-branches,too-many-instance-attributes,protected-access,too-many-positional-arguments

import os
import json
import uuid
from fractions import Fraction
from typing import (
    Any,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from dotenv import load_dotenv
import psycopg

from .base import BaseGraph

from ..utils import (
    EdgeType,
    FloatInt,
    FractionLike,
    VertexType,
    get_z_box_label,
    set_z_box_label,
    vertex_is_z_like,
    vertex_is_zx_like,
)

load_dotenv()

VT = int
ET = Tuple[int, int]


class GraphAGE(BaseGraph[VT, ET]):

    """Apache AGE-backed graph implementation."""

    backend = "age"

    def __init__(self, graph_id: Optional[str] = None):
        BaseGraph.__init__(self)

        self.graph_id = graph_id if graph_id is not None else "test_graph"
        self._vindex: int = 0
        self._inputs: Tuple[VT, ...] = tuple()
        self._outputs: Tuple[VT, ...] = tuple()
        self._maxr: int = 1

<<<<<<< HEAD
        db_uri = os.getenv("DB_URI")
        connect_kwargs = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "dbname": os.getenv("POSTGRES_DB"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
        }
        if db_uri:
            connect_kwargs["conninfo"] = db_uri

        self.conn = psycopg.connect(**connect_kwargs)
        self._session_prepared = False
        self._batch_depth = 0
        self._read_cache_enabled = os.getenv("AGE_READ_CACHE", "1") != "0"
        self._read_cache: dict[str, Any] = {}
        self._prepare_session()
=======
        self.conn = psycopg.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
>>>>>>> experimental

        with self.conn.cursor() as cur:
            try:
                cur.execute(f"SELECT create_graph('{self.graph_id}');")
                self.conn.commit()
            except Exception as e:
                print(f"Error: {e}")
                self.conn.rollback()
<<<<<<< HEAD
                
    def _prepare_session(self) -> None:
        """Prepare AGE session once per DB connection."""
        if self._session_prepared:
            return
=======

    def db_execute(self, query):
>>>>>>> experimental
        with self.conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS age;')
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
        self.conn.commit()
        self._session_prepared = True

    def _fetchone(self, query: str):
        """Execute read query and return one row."""
        cache_key = f"one:{query}"
        if self._read_cache_enabled:
            cached = self._read_cache.get(cache_key, None)
            if cached is not None:
                return cached

        with self.conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
        if self._read_cache_enabled:
            self._read_cache[cache_key] = row
        return row

    def _fetchall(self, query: str):
        """Execute read query and return all rows."""
        cache_key = f"all:{query}"
        if self._read_cache_enabled:
            cached = self._read_cache.get(cache_key, None)
            if cached is not None:
                return cached

        with self.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        if self._read_cache_enabled:
            self._read_cache[cache_key] = rows
        return rows

    def db_execute(self, query: str) -> None:
        """Execute a SQL query with AGE extension and search_path configured."""
        self._read_cache.clear()
        with self.conn.cursor() as cur:
            cur.execute(query)
        if self._batch_depth == 0:
            self.conn.commit()

    def begin_batch(self) -> None:
        """Begin a batched write section (defers commits until end_batch)."""
        self._batch_depth += 1

    def end_batch(self) -> None:
        """End a batched write section and commit on outermost end."""
        if self._batch_depth <= 0:
            return
        self._batch_depth -= 1
        if self._batch_depth == 0:
            self.conn.commit()

    def rollback_batch(self) -> None:
        """Rollback active batched writes and reset batching state."""
        self.conn.rollback()
        self._read_cache.clear()
        self._batch_depth = 0

    def delete_graph(self) -> None:
        """Drop the current AGE graph and all of its data."""
        self._read_cache.clear()
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    "SELECT drop_graph(%s, %s);",
                    (self.graph_id, True)
                )
            except Exception:
                self.conn.rollback()
                return
        self.conn.commit()
        self._read_cache.clear()

    def inputs(self) -> Tuple[VT, ...]:
        """Gets the inputs of the graph."""
        return self._inputs

    def set_inputs(self, inputs: Tuple[VT, ...]):
        """Sets the inputs of the graph."""
        self._inputs = tuple(inputs)

    def outputs(self) -> Tuple[VT, ...]:
        """Gets the outputs of the graph."""
        return self._outputs

    def set_outputs(self, outputs: Tuple[VT, ...]):
        """Sets the outputs of the graph."""
        self._outputs = tuple(outputs)

    def add_vertices(self, amount: int) -> List[VT]:
        """Adds ``amount`` number of vertices and returns a list containing their IDs
        Nodes are stored as (:Node {graph_id, id, t, phase, qubit, row})
        Default values:
            t = VertexType.BOUNDARY
            phase = "0"
            qubit = -1
            row = -1
        """
        if amount < 0:
            raise ValueError("Amount of vertices added must be >= 0")
        if amount == 0:
            return []

        vertex_ids = list(range(self._vindex, self._vindex + amount))
        payload = [
            {
                "id": v_id,
                "t": VertexType.BOUNDARY.value,
                "phase": "0",
                "qubit": -1,
                "row": -1,
            }
            for v_id in vertex_ids
        ]

        def to_cypher_list(data):
            items = []
            for obj in data:
                items.append(
                    "{" +
                    f"id: {obj['id']}, "
                    f"t: {obj['t']}, "
                    f"phase: '{obj['phase']}', "
                    f"qubit: {obj['qubit']}, "
                    f"row: {obj['row']}"
                    + "}"
                )
            return "[" + ", ".join(items) + "]"

        cypher_list = to_cypher_list(payload)

        query = f"""SELECT *
        FROM ag_catalog.cypher('{self.graph_id}', $$
        UNWIND {cypher_list} AS v
        CREATE (n:Node {{
            id: v.id,
            t: v.t,
            phase: v.phase,
            qubit: v.qubit,
            row: v.row
        }})
        RETURN count(n) $$) AS (result agtype);
        """

        self.db_execute(query)

        self._vindex += amount
        return vertex_ids
<<<<<<< HEAD
=======
    def add_vertex(self, ty: VertexType, qubit: int = 0, row: int = 0, phase: Fraction = None):
        """Add a vertex to the AGE graph"""
        props = f"ty:'{ty.name}', qubit:{qubit}, row:{row}"
        if phase is not None:
            props += f", phase:{float(phase)}"
        props += "}"
        query = (
            f"SELECT * FROM cypher('{self.graph_id}', $$ "
            f"CREATE (n:{ty.name} {props}) "
            "RETURN id(n) $$) AS (id agtype)"
        )
        with self.conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()
        if row is None:
            raise RuntimeError("Failed to create vertex; no id returned")
        vertex_id = str(row[0]).split("::", 1)[0].strip('"')
        return int(vertex_id)
>>>>>>> experimental

    def add_vertex(
        self,
        ty: VertexType = VertexType.BOUNDARY,
        qubit: FloatInt = -1,
        row: FloatInt = -1,
        phase: Optional[FractionLike] = None,
        ground: bool = False,
        index: Optional[VT] = None,
    ) -> VT:
        """Add a single vertex to the graph and return its index."""
        if phase is None:
            if ty == VertexType.H_BOX:
                phase = 1
            else:
                phase = 0
        try:
            phase = phase % 2
        except Exception:
            pass
        phase_str = str(phase)

        if index is not None:
            self.add_vertex_indexed(index)
            v = index
            query = f"""
            SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
                MATCH (n:Node {{id: {v}}})
                SET n.t = {ty.value},
                    n.qubit = {qubit},
                    n.row = {row},
                    n.phase = '{phase_str}'
                REMOVE n.ty
                RETURN count(n)
            $$) AS (count agtype);
            """
            self.db_execute(query)
        else:
            v = self._vindex
            query = f"""
            SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
                CREATE (n:Node {{
                    id: {v},
                    t: {ty.value},
                    phase: '{phase_str}',
                    qubit: {qubit},
                    row: {row}
                }})
                RETURN count(n)
            $$) AS (count agtype);
            """
            self.db_execute(query)
            self._vindex += 1

        if ground:
            self.set_ground(v, True)
        if self.track_phases:
            self.max_phase_index += 1
            self.phase_index[v] = self.max_phase_index
            self.phase_mult[self.max_phase_index] = 1
        return v

    def add_vertex_indexed(self, v: VT) -> None:
        """Adds a vertex with a guaranteed index.

        Raises ValueError if the index is already in use.
        """
        q_exists = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {v}}})
            RETURN count(n)
        $$) AS (count agtype);
        """
        row = self._fetchone(q_exists)

        if row and int(str(row[0]).split("::", 1)[0].strip('"')) > 0:
            raise ValueError("Vertex with this index already exists")

        q_create = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            CREATE (n:Node {{
                id: {v},
                t: {VertexType.BOUNDARY.value},
                phase: '0',
                qubit: -1,
                row: -1
            }})
            RETURN count(n)
        $$) AS (count agtype);
        """
        self.db_execute(q_create)

        if v >= self._vindex:
            self._vindex = v + 1

    def add_edge(  # noqa: too-many-branches
        self, edge_pair: Tuple[VT, VT], edgetype: EdgeType = EdgeType.SIMPLE
    ) -> ET:
        """Add a single edge of the given type and return its canonical id.

        Mirrors graph_s.py: direction is always normalised to min→max,
        and parallel edges are resolved via the Hopf / spider laws.
        """
        s, t = edge_pair

        # ── self-loops ──────────────────────────────────────────────────────
        if s == t:
            t1 = self.type(s)
            if not vertex_is_zx_like(t1):
                raise ValueError(
                    f"Cannot add self-loop on non-ZX vertex {s} (type {t1})"
                )
            if edgetype == EdgeType.SIMPLE:
                return self.edge(s, s)  # simple self-loop is a no-op
            if edgetype == EdgeType.HADAMARD:
                self.add_to_phase(s, 1)
                return self.edge(s, s)
            raise ValueError(f"Unexpected edge type {edgetype} for self-loop")

        # ── normalise direction ──────────────────────────────────────────────
        src, dst = (s, t) if s < t else (t, s)

        if not self.connected(src, dst):
            # ── no existing edge: create it ──────────────────────────────────
            query = f"""
            SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
                MATCH (a:Node {{id: {src}}}), (b:Node {{id: {dst}}})
                CREATE (a)-[e:Wire {{t: {int(edgetype)}}}]->(b)
                RETURN count(e)
            $$) AS (count agtype);
            """
            self.db_execute(query)
        else:
            # ── parallel edge: apply Hopf / spider laws ──────────────────────
            t1 = self.type(src)
            t2 = self.type(dst)
            if vertex_is_zx_like(t1) and vertex_is_zx_like(t2):
                et1 = self.edge_type(self.edge(src, dst))
                # same colour → SIMPLE is 'fuse', HADAMARD is 'hopf'
                if vertex_is_z_like(t1) == vertex_is_z_like(t2):
                    fuse, hopf = EdgeType.SIMPLE, EdgeType.HADAMARD
                else:
                    fuse, hopf = EdgeType.HADAMARD, EdgeType.SIMPLE

                if edgetype == fuse and et1 == fuse:
                    pass  # two fuse-type edges → keep one (no-op)
                elif (edgetype == fuse and et1 == hopf) or (
                    edgetype == hopf and et1 == fuse
                ):
                    # one of each → keep fuse edge, add π to src, scalar ×½
                    self.set_edge_type((src, dst), fuse)
                    if t1 == VertexType.Z_BOX:
                        set_z_box_label(
                            self, src, get_z_box_label(self, src) * -1
                        )
                    else:
                        self.add_to_phase(src, 1)
                    self.scalar.add_power(-1)
                elif edgetype == hopf and et1 == hopf:
                    # two hopf-type edges → remove edge, scalar ×¼
                    self.remove_edge(self.edge(src, dst))
                    self.scalar.add_power(-2)
                else:
                    raise ValueError(
                        f"Unexpected edge types: {edgetype}, {et1} for "
                        f"vertices {src}({t1}), {dst}({t2})"
                    )
            else:
                # H-box / non-ZX-like boundary — simple parallel just reduces
                if (
                    vertex_is_z_like(t1) and t2 == VertexType.H_BOX
                ) or (
                    vertex_is_z_like(t2) and t1 == VertexType.H_BOX
                ):
                    if edgetype == EdgeType.SIMPLE:
                        return self.edge(src, dst)  # single simple edge kept
                raise ValueError(
                    f"Attempted to add unreducible parallel edge {edge_pair}, "
                    f"types: {t1}, {t2}"
                )

        return self.edge(src, dst)

    def remove_vertices(self, vertices):
        """Removes the specified vertices from the graph."""
        vertex_list = list(vertices)
        if not vertex_list:
            return

        # Build a list of vertex IDs to match in Cypher
        # Using a WHERE clause with INs to match multiple vertices
        vertex_ids_str = ", ".join(str(v) for v in vertex_list)

        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node) WHERE n.id IN [{vertex_ids_str}]
            DETACH DELETE n
            RETURN count(n)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def remove_edges(self, edges):
        """Removes relationships from the graph."""
        edge_list = list(edges)
        if not edge_list:
            return

        # Build Cypher list for edge pairs
        edges_list = []
        for s, t in edge_list:
            edges_list.append(f"{{s: {s}, t: {t}}}")
        edges_str = "[" + ", ".join(edges_list) + "]"

        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            UNWIND {edges_str} AS e
            MATCH (n1:Node {{id: e.s}})-[r:Wire]-(n2:Node {{id: e.t}})
            DELETE r
            RETURN count(r)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def num_vertices(self) -> int:
        """Returns the number of vertices in the graph."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node)
            RETURN count(n)
        $$) AS (count agtype);
        """
        row = self._fetchone(query)
        if row:
            return int(str(row[0]).split("::", 1)[0].strip('"'))
        return 0

    def vindex(self) -> int:
        """Returns the next fresh vertex index."""
        return self._vindex

    def num_edges(
        self,
        s: Optional[VT] = None,
        t: Optional[VT] = None,
        et: Optional[EdgeType] = None,
    ) -> int:
        """Returns the number of edges in the graph.

        If source and target vertices are given, counts edges between them.
        If edge type is given, counts only edges of that type.
        """
        if s is not None and t is not None:
            # Count edges between two specific vertices
            s, t = (s, t) if s <= t else (t, s)
            if et is not None:
                query = f"""
                SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
                    MATCH (n1:Node {{id: {s}}})-[r:Wire {{t: {et.value}}}]->(n2:Node {{id: {t}}})
                    RETURN count(r)
                $$) AS (count agtype);
                """
            else:
                query = f"""
                SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
                    MATCH (n1:Node {{id: {s}}})-[r:Wire]->(n2:Node {{id: {t}}})
                    RETURN count(r)
                $$) AS (count agtype);
                """
        else:
            # Count all edges
            query = f"""
            SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
                MATCH ()-[r:Wire]->()
                RETURN count(r)
            $$) AS (count agtype);
            """

        row = self._fetchone(query)
        if row:
            return int(str(row[0]).split("::", 1)[0].strip('"'))
        return 0

    def depth(self) -> int:
        """Returns the maximum non-negative row index, or -1 if unavailable."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node)
            WHERE n.row IS NOT NULL AND n.row >= 0
            RETURN max(n.row)
        $$) AS (maxr agtype);
        """
        row = self._fetchone(query)

        if not row or row[0] is None:
            self._maxr = -1
            return self._maxr

        maxr = str(row[0]).split("::", 1)[0].strip('"')
        if maxr in ("", "null"):
            self._maxr = -1
        else:
            self._maxr = int(float(maxr))
        return self._maxr

    def remove_isolated_vertices(self) -> None:
        """Deletes isolated vertices and isolated pairs, updating scalar accordingly."""
        rem: List[VT] = []

        for v in list(self.vertices()):
            d = self.vertex_degree(v)
            if d == 0:
                rem.append(v)
                ty = self.type(v)
                if ty == VertexType.BOUNDARY:
                    raise TypeError(
                        "Diagram is not a well-typed ZX-diagram: contains isolated boundary vertex."
                    )
                if ty == VertexType.H_BOX:
                    self.scalar.add_phase(self.phase(v))
                else:
                    self.scalar.add_node(self.phase(v))

            if d == 1:
                if v in rem:
                    continue
                if self.type(v) == VertexType.BOUNDARY:
                    continue

                neigh = list(self.neighbors(v))
                if not neigh:
                    continue
                w = neigh[0]

                if len(list(self.neighbors(w))) > 1:
                    continue
                if self.type(w) == VertexType.BOUNDARY:
                    continue

                rem.append(v)
                rem.append(w)
                et = self.edge_type(self.edge(v, w))
                t1 = self.type(v)
                t2 = self.type(w)
                if t1 == VertexType.H_BOX:
                    t1 = VertexType.Z
                if t2 == VertexType.H_BOX:
                    t2 = VertexType.Z

                if t1 == t2:
                    if et == EdgeType.SIMPLE:
                        self.scalar.add_node(self.phase(v) + self.phase(w))
                    else:
                        self.scalar.add_spider_pair(self.phase(v), self.phase(w))
                else:
                    if et == EdgeType.SIMPLE:
                        self.scalar.add_spider_pair(self.phase(v), self.phase(w))
                    else:
                        self.scalar.add_node(self.phase(v) + self.phase(w))

        self.remove_vertices(rem)

    def vertices(self) -> Iterable[VT]:
        """Iterator over all the vertices."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node) WHERE n.id IS NOT NULL RETURN n.id
        $$) AS (id agtype);
        """
        rows = self._fetchall(query)

        return [int(str(row[0]).split("::", 1)[0].strip('"')) for row in rows]

    def edges(self, s: Optional[VT] = None, t: Optional[VT] = None) -> Iterable[ET]:
        """Iterator that returns all the edges in the graph,
        or all the edges connecting the pair of vertices.
        Output type depends on implementation in backend."""

        if s is not None and t is not None:
            query = f"""
            SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
                MATCH (n1:Node {{id: {s}}})-[r:Wire]-(n2:Node {{id: {t}}})
                RETURN n1.id AS src, n2.id AS tgt
            $$) AS (src agtype, tgt agtype);
            """
            rows = self._fetchall(query)
            return [(int(str(row[0]).split("::", 1)[0].strip('"')),
                     int(str(row[1]).split("::", 1)[0].strip('"'))) for row in rows]

        # Return all edges, canonicalized by ID to avoid duplicates
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n1:Node)-[r:Wire]-(n2:Node)
            WHERE n1.id <= n2.id
            RETURN n1.id AS s, n2.id AS t
        $$) AS (s agtype, t agtype);
        """
        rows = self._fetchall(query)
        return [(int(str(row[0]).split("::", 1)[0].strip('"')),
                 int(str(row[1]).split("::", 1)[0].strip('"'))) for row in rows]

    def edge(self, s: VT, t: VT, et: EdgeType = EdgeType.SIMPLE) -> ET:
        """Returns the edge between vertices s and t (canonicalized as tuple)."""
        del et
        return (s, t) if s < t else (t, s)

    def edge_st(self, edge: ET) -> Tuple[VT, VT]:
        """Returns a tuple of source/target of the given edge."""
        return edge

    def edge_s(self, edge: ET) -> VT:
        """Returns the source of the given edge."""
        return self.edge_st(edge)[0]

    def edge_t(self, edge: ET) -> VT:
        """Returns the target of the given edge."""
        return self.edge_st(edge)[1]

    def connected(self, v1: VT, v2: VT) -> bool:
        """Returns whether vertices v1 and v2 share an edge."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n1:Node {{id: {v1}}})-[r:Wire]-(n2:Node {{id: {v2}}})
            RETURN count(r)
        $$) AS (count agtype);
        """
        row = self._fetchone(query)

        if not row:
            return False
        return int(str(row[0]).split("::", 1)[0].strip('"')) > 0

    def neighbors(self, vertex: VT) -> Sequence[VT]:
        """Returns all neighboring vertices of the given vertex."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n)-[r:Wire]-(m)
            WHERE n.id = {vertex}
            RETURN m.id
        $$) AS (id agtype);
        """
        rows = self._fetchall(query)

        neighbors = {
            int(str(row[0]).split("::", 1)[0].strip('"'))
            for row in rows
        }
        return list(neighbors)

    def vertex_degree(self, vertex: VT) -> int:
        """Returns the degree of the given vertex."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n)-[r:Wire]-()
            WHERE n.id = {vertex}
            RETURN count(r)
        $$) AS (count agtype);
        """
        row = self._fetchone(query)

        if row:
            return int(str(row[0]).split("::", 1)[0].strip('"'))
        return 0

    def incident_edges(self, vertex: VT) -> Sequence[ET]:
        """Returns all neighboring edges of the given vertex."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n)-[r:Wire]-(m)
            WHERE n.id = {vertex}
            RETURN n.id, m.id
        $$) AS (src agtype, tgt agtype);
        """
        rows = self._fetchall(query)

        return [
            (int(str(row[0]).split("::", 1)[0].strip('"')),
             int(str(row[1]).split("::", 1)[0].strip('"')))
            for row in rows
        ]

    def edge_type(self, e: ET) -> EdgeType:
        """Returns the type of the given edge.

        Raises KeyError if the edge is not in the graph.
        """
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n1:Node {{id: {e[0]}}})-[r:Wire]-(n2:Node {{id: {e[1]}}})
            RETURN r.t
        $$) AS (t agtype);
        """
        row = self._fetchone(query)

        if not row:
            raise KeyError(f"{e} has no edge type")

        edge_type_raw = str(row[0]).split("::", 1)[0].strip('"')
        if edge_type_raw in ("", "null", "None"):
            return EdgeType.SIMPLE

        return EdgeType(int(float(edge_type_raw)))

    def set_edge_type(self, e: ET, t: EdgeType) -> None:
        """Sets the type of the given edge."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n1:Node {{id: {e[0]}}})-[r:Wire]-(n2:Node {{id: {e[1]}}})
            SET r.t = {t.value}
            RETURN count(r)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def type(self, vertex: VT) -> VertexType:
        """Returns the type of the given vertex."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            RETURN n.t, n.ty
        $$) AS (t agtype, ty agtype);
        """
        row = self._fetchone(query)

        if not row:
            raise KeyError(f"{vertex} has no type")

        t_raw = str(row[0]).split("::", 1)[0].strip('"')
        if t_raw not in ("", "null", "None"):
            return VertexType(int(float(t_raw)))

        ty_raw = str(row[1]).split("::", 1)[0].strip('"')
        if ty_raw not in ("", "null", "None"):
            return VertexType[ty_raw]

        raise KeyError(f"{vertex} has no type")

    def types(self) -> Mapping[VT, VertexType]:
        """Returns a mapping of vertices to their types."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node)
            RETURN n.id, n.t, n.ty
        $$) AS (id agtype, t agtype, ty agtype);
        """
        rows = self._fetchall(query)

        result: dict[VT, VertexType] = {}
        for row in rows:
            vertex = int(str(row[0]).split("::", 1)[0].strip('"'))
            t_raw = str(row[1]).split("::", 1)[0].strip('"')
            if t_raw not in ("", "null", "None"):
                result[vertex] = VertexType(int(float(t_raw)))
                continue

            ty_raw = str(row[2]).split("::", 1)[0].strip('"')
            if ty_raw not in ("", "null", "None"):
                result[vertex] = VertexType[ty_raw]
                continue

            raise KeyError(f"{vertex} has no type")

        return result

    def set_type(self, vertex: VT, t: VertexType) -> None:
        """Sets the type of the given vertex to t."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            SET n.t = {t.value}
            REMOVE n.ty
            RETURN count(n)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def phase(self, vertex: VT) -> FractionLike:
        """Returns the phase value of the given vertex."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            RETURN n.phase
        $$) AS (phase agtype);
        """
        row = self._fetchone(query)

        if not row:
            return Fraction(0)

        phase_raw = str(row[0]).split("::", 1)[0].strip('"')
        if phase_raw in ("", "null", "None"):
            return Fraction(0)

        try:
            return Fraction(phase_raw).limit_denominator(10**9)
        except ValueError:
            return Fraction(0)

    def phases(self) -> Mapping[VT, FractionLike]:
        """Returns a mapping of vertices to their phase values."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node)
            RETURN n.id, n.phase
        $$) AS (id agtype, phase agtype);
        """
        rows = self._fetchall(query)

        result: dict[VT, FractionLike] = {}
        for row in rows:
            vertex = int(str(row[0]).split("::", 1)[0].strip('"'))
            phase_raw = str(row[1]).split("::", 1)[0].strip('"')
            if phase_raw in ("", "null", "None"):
                result[vertex] = Fraction(0)
                continue
            try:
                result[vertex] = Fraction(phase_raw).limit_denominator(10**9)
            except ValueError:
                result[vertex] = Fraction(0)

        return result

    def set_phase(self, vertex: VT, phase: FractionLike) -> None:
        """Sets the phase of the given vertex."""
        try:
            phase = phase % 2
        except Exception:
            pass
        phase_str = str(phase)
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            SET n.phase = '{phase_str}'
            RETURN count(n)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def qubit(self, vertex: VT) -> FloatInt:
        """Returns the qubit index associated to the vertex.
        If no index has been set, returns -1."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            RETURN n.qubit
        $$) AS (qubit agtype);
        """
        row = self._fetchone(query)

        if not row:
            return -1

        qubit_raw = str(row[0]).split("::", 1)[0].strip('"')
        if qubit_raw in ("", "null", "None"):
            return -1

        val = float(qubit_raw)
        return int(val) if val == int(val) else val

    def qubits(self) -> Mapping[VT, FloatInt]:
        """Returns a mapping of vertices to their qubit indices."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node)
            RETURN n.id, n.qubit
        $$) AS (id agtype, qubit agtype);
        """
        rows = self._fetchall(query)

        result: dict[VT, FloatInt] = {}
        for row in rows:
            vertex = int(str(row[0]).split("::", 1)[0].strip('"'))
            qubit_raw = str(row[1]).split("::", 1)[0].strip('"')
            if qubit_raw in ("", "null", "None"):
                result[vertex] = -1
                continue
            val = float(qubit_raw)
            result[vertex] = int(val) if val == int(val) else val

        return result

    def set_qubit(self, vertex: VT, q: FloatInt) -> None:
        """Sets the qubit index associated to the vertex."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            SET n.qubit = {q}
            RETURN count(n)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def row(self, vertex: VT) -> FloatInt:
        """Returns the row index associated to the vertex.
        If no index has been set, returns -1."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            RETURN n.row
        $$) AS (row agtype);
        """
        row = self._fetchone(query)

        if not row:
            return -1

        row_raw = str(row[0]).split("::", 1)[0].strip('"')
        if row_raw in ("", "null", "None"):
            return -1

        val = float(row_raw)
        return int(val) if val == int(val) else val

    def rows(self) -> Mapping[VT, FloatInt]:
        """Returns a mapping of vertices to their row indices."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node)
            RETURN n.id, n.row
        $$) AS (id agtype, row agtype);
        """
        rows = self._fetchall(query)

        result: dict[VT, FloatInt] = {}
        for row in rows:
            vertex = int(str(row[0]).split("::", 1)[0].strip('"'))
            row_raw = str(row[1]).split("::", 1)[0].strip('"')
            if row_raw in ("", "null", "None"):
                result[vertex] = -1
                continue
            val = float(row_raw)
            result[vertex] = int(val) if val == int(val) else val

        return result

    def set_row(self, vertex: VT, r: FloatInt) -> None:
        """Sets the row index associated to the vertex."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            SET n.row = {r}
            RETURN count(n)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def vdata_keys(self, vertex: VT) -> Sequence[str]:
        """Returns an iterable of the vertex data key names."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            RETURN keys(n)
        $$) AS (keys agtype);
        """
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

<<<<<<< HEAD
        if not row:
            return []

        keys_raw = str(row[0]).split("::", 1)[0]
        if keys_raw in ("", "null", "None"):
            return []

        try:
            parsed = json.loads(keys_raw)
            if isinstance(parsed, list):
                return [str(k) for k in parsed]
        except json.JSONDecodeError:
            pass
        return []

    def vdata(self, vertex: VT, key: str, default: Any = None) -> Any:
        """Returns the data value of the given vertex associated to the key.
        If this key has no value associated with it, returns the default value."""
        key_escaped = key.replace("'", "\\'")
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            RETURN n['{key_escaped}']
        $$) AS (value agtype);
        """
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

        if not row:
            return default

        value_raw = str(row[0]).split("::", 1)[0]
        if value_raw in ("", "null", "None"):
            return default

        try:
            parsed = json.loads(value_raw)
            return default if parsed is None else parsed
        except json.JSONDecodeError:
            return value_raw.strip('"')

    def set_vdata(self, vertex: VT, key: str, val: Any) -> None:
        """Sets the vertex data associated to key to val."""
        key_escaped = key.replace("`", "``")

        if val is None:
            value_expr = "null"
        elif isinstance(val, bool):
            value_expr = "true" if val else "false"
        elif isinstance(val, (int, float)):
            value_expr = str(val)
        else:
            value_escaped = str(val).replace("\\", "\\\\").replace("'", "\\'")
            value_expr = f"'{value_escaped}'"

        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            SET n.`{key_escaped}` = {value_expr}
            RETURN count(n)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def clear_vdata(self, vertex: VT) -> None:
        """Removes all vdata associated to a vertex."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node {{id: {vertex}}})
            SET n = {{id: n.id, t: n.t}}
            RETURN count(n)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def edata(self, edge: ET, key: str, default: Any = None) -> Any:
        """Returns the data value of the given edge associated to the key.
        If this key has no value associated with it, returns the default value."""
        key_escaped = key.replace("'", "\\'")
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n1:Node {{id: {edge[0]}}})-[r:Wire]-(n2:Node {{id: {edge[1]}}})
            RETURN r['{key_escaped}']
        $$) AS (value agtype);
        """
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

        if not row:
            return default

        value_raw = str(row[0]).split("::", 1)[0]
        if value_raw in ("", "null", "None"):
            return default

        try:
            parsed = json.loads(value_raw)
            return default if parsed is None else parsed
        except json.JSONDecodeError:
            return value_raw.strip('"')

    def set_edata(self, edge: ET, key: str, val: Any) -> None:
        """Sets the edge data associated to key to val."""
        key_escaped = key.replace("`", "``")

        if val is None:
            value_expr = "null"
        elif isinstance(val, bool):
            value_expr = "true" if val else "false"
        elif isinstance(val, (int, float)):
            value_expr = str(val)
        else:
            value_escaped = str(val).replace("\\", "\\\\").replace("'", "\\'")
            value_expr = f"'{value_escaped}'"

        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n1:Node {{id: {edge[0]}}})-[r:Wire]-(n2:Node {{id: {edge[1]}}})
            SET r.`{key_escaped}` = {value_expr}
            RETURN count(r)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def clear_edata(self, edge: ET) -> None:
        """Removes all edata associated to an edge."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n1:Node {{id: {edge[0]}}})-[r:Wire]-(n2:Node {{id: {edge[1]}}})
            SET r = {{t: r.t}}
            RETURN count(r)
        $$) AS (count agtype);
        """
        self.db_execute(query)

    def edata_keys(self, edge: ET) -> Sequence[str]:
        """Returns an iterable of the edge data key names."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n1:Node {{id: {edge[0]}}})-[r:Wire]-(n2:Node {{id: {edge[1]}}})
            RETURN keys(r)
        $$) AS (keys agtype);
        """
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

        if not row:
            return []

        keys_raw = str(row[0]).split("::", 1)[0]
        if keys_raw in ("", "null", "None"):
            return []

        try:
            parsed = json.loads(keys_raw)
            if isinstance(parsed, list):
                return [str(k) for k in parsed]
        except json.JSONDecodeError:
            pass
        return []

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    def clone(self) -> "GraphAGE":
        """Return an identical copy of the graph without relabeling vertices/edges."""
        new_graph_id = f"{self.graph_id}_clone_{uuid.uuid4().hex}"
        cpy = GraphAGE(graph_id=new_graph_id)

        cpy.scalar = self.scalar.copy()
        cpy.track_phases = self.track_phases
        cpy.phase_index = self.phase_index.copy()
        cpy.phase_master = self.phase_master
        cpy.phase_mult = self.phase_mult.copy()
        cpy.max_phase_index = self.max_phase_index
        cpy.merge_vdata = self.merge_vdata

        cpy._vindex = self._vindex
        cpy._maxr = self._maxr

        base_vprops = {"id", "t", "ty", "phase", "qubit", "row"}
        base_eprops = {"id", "t"}

        for v in self.vertices():
            cpy.add_vertex_indexed(v)
            cpy.set_type(v, self.type(v))
            cpy.set_qubit(v, self.qubit(v))
            cpy.set_row(v, self.row(v))
            cpy.set_phase(v, self.phase(v))
            for key in self.vdata_keys(v):
                if key in base_vprops:
                    continue
                cpy.set_vdata(v, key, self.vdata(v, key))

        for e in self.edges():
            new_e = cpy.add_edge(e, self.edge_type(e))
            for key in self.edata_keys(e):
                if key in base_eprops:
                    continue
                cpy.set_edata(new_e, key, self.edata(e, key))

        cpy.set_inputs(self.inputs())
        cpy.set_outputs(self.outputs())
        return cpy
=======
    def close(self):
        self.conn.close()
>>>>>>> experimental
