"""
Docstring for pyzx.graph.graph_neo4j
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

class GraphAGE:
    def __init__(
        self, 
        database = os.getenv("POSTGRES_DB", "age_db"),
        user = os.getenv("POSTGRES_USER", "postgres"),
        host = os.getenv("DB_HOST", "age"),
        password = os.getenv("POSTGRES_PASSWORD", ""), 
        port=5432, 
        graph_id="test_graph"
        ):
        print(database, user, host, password, port)
        self.conn = psycopg.connect(
            dbname=database,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.graph_id = graph_id
        with self.conn.cursor() as cur:
            cur.execute('SET search_path = ag_catalog, "$user", public;')
            cur.execute(f"SELECT drop_graph('{self.graph_id}', true);")
            cur.execute(f"SELECT create_graph('{self.graph_id}')")
            self.conn.commit()

    def add_vertex(self, ty: VertexType, qubit: int = 0, row: int = 0, phase: Fraction = None):
        """Add a vertex to the AGE graph"""
        props = f"{{ty:'{ty.name}', qubit:{qubit}, row:{row}"
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