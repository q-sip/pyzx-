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

        self.conn = psycopg.connect(
            host = os.getenv("DB_HOST"),
            port = os.getenv("DB_PORT"),
            conninfo = os.getenv("DB_URI"),
            dbname = os.getenv("POSTGRES_DB"),
            user = os.getenv("POSTGRES_USER"),
            password = os.getenv("POSTGRES_PASSWORD")
            )

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

    def close(self):
        self.conn.close()