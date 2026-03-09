"""
Docstring for pyzx.graph.graph_AGE
"""

import os
import uuid
import psycopg

from pyzx.utils import VertexType, EdgeType
from fractions import Fraction
from typing import (
    Any,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

# testing pylint
from dotenv import load_dotenv
#To be replaced
#from neo4j import GraphDatabase

from pyzx.symbolic import new_var, parse
from .graph_db_rewrite_runner import run_rewrite

from .base import BaseGraph, upair

from ..utils import (
    EdgeType,
    FloatInt,
    FractionLike,
    VertexType,
    vertex_is_zx_like,
    vertex_is_z_like,
    set_z_box_label,
    get_z_box_label,
)
from .base import BaseGraph, upair

load_dotenv()

VT = int
ET = Tuple[int, int]

class GraphAGE(BaseGraph[VT,ET]):

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
            self.conn.commit() # ENSURE LOAD IS COMMITTED

            # 2. Create graph (search_path is already set in options)
            try:
                cur.execute(f"SELECT create_graph('{self.graph_id}');")
                self.conn.commit()
            except Exception as e:
                print(f"Error: {e}")
                self.conn.rollback()
    
    def db_execute(self, query):
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
        self.conn.commit()

    def delete_graph(self):
        with self.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(
                "SELECT drop_graph(%s, %s);",
                (self.graph_id, True)
            )
        self.conn.commit()
        print("Graph deleted")

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

        query = (f"""SELECT *
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
        """)

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

    def add_edge(self, src, dst, edge_type: EdgeType):
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

    def close(self):
        self.conn.close()