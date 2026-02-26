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

class GraphAGE:
    def __init__(self):
        user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER")
        password = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD")
        self.conn = psycopg.connect(

            host = os.getenv("DB_HOST"),
            port = os.getenv("DB_PORT"),
            dbname = os.getenv("POSTGRES_DB"),
            user = os.getenv("DB_USER"),
            password = os.getenv("DB_PASSWORD")
            )

        graph = BaseGraph()


        host=os.getenv("DB_HOST", "age"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "age_db"),
        user=user,
        password=password,
        

        self.graph_id = "test_graph"

        with self.conn.cursor() as cur:
            # 1. Load extension
            cur.execute('CREATE EXTENSION IF NOT EXISTS age;')
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path TO ag_catalog;")
            self.conn.commit() # ENSURE LOAD IS COMMITTED

            # 2. Create graph (search_path is already set in options)
            try:
                #cur.execute(f"SELECT create_graph('{self.graph_id}');")
                cur.execute(f"select COUNT(*) from age_db.ag_catalog.ag_graph ag ;")
                count = cur.fetchone()[0]
                cur.execute(f"SELECT create_graph('koira{count}');")
                self.conn.commit()
            except Exception as e:
                print(f"Error: {e}")
                self.conn.rollback()

#        self.graph_id = "test_graph"
#        connection = age.connect(graph=GRAPH_NAME, dsn=CONFIG)

#        self.conn("CREATE EXTENSION age;")
#        self.conn("LOAD 'age';")
#        self.conn("CREATE EXTENSION age;")

#        self.conn("SELECT create_graph({self.graph.id});")
        
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