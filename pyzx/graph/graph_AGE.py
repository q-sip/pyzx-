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
        #print(database, user, host, password, port)
        self.conn = psycopg.connect(
            dbname=database,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.graph_id = graph_id
        
        with self.conn.cursor() as cur:
            # Ensure AGE extension is loaded
            try:
                cur.execute('CREATE EXTENSION IF NOT EXISTS age;')
                self.conn.commit()
            except Exception as e:
                print(f"Warning: CREATE EXTENSION failed: {e}")
                self.conn.rollback()
            
            # Reset the search path
            try:
                cur.execute('SET search_path = ag_catalog, "$user", public;')
            except Exception as e:
                print(f"Warning: SET search_path failed: {e}")
                self.conn.rollback()
            
            # Drop existing graph if it exists
            try:
                cur.execute(f"SELECT ag_catalog.drop_graph('{self.graph_id}'::name, true);")
                self.conn.commit()
            except Exception as e:
                # Graph doesn't exist, which is fine
                print(f"Info: drop_graph note: {e}")
                self.conn.rollback()
            
            # Create new graph
            try:
                cur.execute(f"SELECT ag_catalog.create_graph('{self.graph_id}'::name)")
                self.conn.commit()
                print(f"Successfully created AGE graph: {self.graph_id}")
            except Exception as e:
                print(f"Error: create_graph failed: {type(e).__name__}: {e}")
                print("AGE extension may not be properly installed in the database.")
                self.conn.rollback()
    
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
