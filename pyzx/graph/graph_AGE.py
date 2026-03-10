"""
Docstring for pyzx.graph.graph_AGE
"""

# pylint: disable=invalid-name,abstract-method,arguments-differ,no-member,super-init-not-called,broad-exception-caught,too-many-public-methods

import os
import json
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
)

load_dotenv()

VT = int
ET = Tuple[int, int]


class GraphAGE(BaseGraph[VT, ET]):

    """Apache AGE-backed graph implementation."""

    backend = "age"

    def __init__(self):

        self.graph_id = "test_graph"
        self._vindex: int = 0
        self._inputs: Tuple[VT, ...] = tuple()
        self._outputs: Tuple[VT, ...] = tuple()
        self._maxr: int = 1

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

        with self.conn.cursor() as cur:
            # 1. Load extension
            cur.execute('CREATE EXTENSION IF NOT EXISTS age;')
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path TO ag_catalog;")
            self.conn.commit()

            # 2. Create graph (search_path is already set in options)
            try:
                cur.execute(f"SELECT create_graph('{self.graph_id}');")
                self.conn.commit()
            except Exception as e:
                print(f"Error: {e}")
                self.conn.rollback()

    def db_execute(self, query: str) -> None:
        """Execute a SQL query with AGE extension and search_path configured."""
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
        self.conn.commit()

    def delete_graph(self) -> None:
        """Drop the current AGE graph and all of its data."""
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(
                "SELECT drop_graph(%s, %s);",
                (self.graph_id, True)
            )
        self.conn.commit()

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

    def depth(self) -> int:
        """Returns the maximum non-negative row index, or -1 if unavailable."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node)
            WHERE n.row IS NOT NULL AND n.row >= 0
            RETURN max(n.row)
        $$) AS (maxr agtype);
        """
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

        if not row or row[0] is None:
            self._maxr = -1
            return self._maxr

        maxr = str(row[0]).split("::", 1)[0].strip('"')
        if maxr in ("", "null"):
            self._maxr = -1
        else:
            self._maxr = int(float(maxr))
        return self._maxr

    def vertices(self) -> Iterable[VT]:
        """Iterator over all the vertices."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.graph_id}', $$
            MATCH (n:Node) WHERE n.id IS NOT NULL RETURN n.id
        $$) AS (id agtype);
        """
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            rows = cur.fetchall()
            self.conn.commit()

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
            with self.conn.cursor() as cur:
                cur.execute("LOAD 'age';")
                cur.execute("SET search_path = ag_catalog, public;")
                cur.execute(query)
                rows = cur.fetchall()
                self.conn.commit()
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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            rows = cur.fetchall()
            self.conn.commit()
        return [(int(str(row[0]).split("::", 1)[0].strip('"')),
                 int(str(row[1]).split("::", 1)[0].strip('"'))) for row in rows]

    def edge(self, s: VT, t: VT) -> ET:
        """Returns the edge between vertices s and t (canonicalized as tuple)."""
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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            rows = cur.fetchall()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            rows = cur.fetchall()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            rows = cur.fetchall()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            rows = cur.fetchall()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            rows = cur.fetchall()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            rows = cur.fetchall()
            self.conn.commit()

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

    def add_edge(self, src: VT, dst: VT, edge_type: EdgeType):
        """Add an edge between vertices"""
        query = f"""
        SELECT * FROM cypher('{self.graph_id}', $$
            MATCH (a),(b) WHERE id(a)={src} AND id(b)={dst}
            CREATE (a)-[e:{edge_type.name}]->(b)
            RETURN id(e)
        $$) AS (id agtype)
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()
        if row is None:
            raise ValueError(f"No edge created; check vertex ids {src}, {dst}")
        edge_id = str(row[0]).split("::", 1)[0].strip('"')
        return int(edge_id)

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
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()
        if row:
            return int(str(row[0]).split("::", 1)[0].strip('"'))
        return 0

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

        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.conn.commit()
        if row:
            return int(str(row[0]).split("::", 1)[0].strip('"'))
        return 0

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
