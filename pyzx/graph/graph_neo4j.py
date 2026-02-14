# COMPLETELY WORKING IMPLEMENTATION FOR ALL THREE DEPTHS!!!!!

#WORKING IMPLEMENTATION!!!

"""
Docstring for pyzx.graph.graph_neo4j
"""

import os
import uuid
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
from neo4j import GraphDatabase

from pyzx.symbolic import new_var, parse
from .neo4j_rewrite_runner import run_rewrite

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


class GraphNeo4j(BaseGraph[VT, ET]):
    """Implementation of the BaseGraph interface using Neo4j as the backend.
    This class manages a graph instance stored within a Neo4j database."""

    backend = "neo4j"

    def __init__(
        self,
        uri: str = os.getenv("NEO4J_URI", ""),
        user: str = os.getenv("NEO4J_USER", ""),
        password: str = os.getenv("NEO4J_PASSWORD", ""),
        graph_id: Optional[str] = None,
        database: Optional[str] = None,
    ):
        BaseGraph.__init__(self)
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self._driver = None

        self.graph_id = graph_id if graph_id is not None else "graph_" + str(id(self))
        # Clear any existing data for this ID to be safe (id reuse)
        if graph_id is None:
            self.remove_all_data()

        self._vindex: int = 0
        self._inputs: Tuple[VT, ...] = tuple()
        self._outputs: Tuple[VT, ...] = tuple()
        self._maxr: int = 1

    # Avaa ja sulkee neo4j driverin, suoraan Valterin reposta
    @property
    def driver(self):
        """Create driver only when needed"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        return self._driver

    def remove_all_data(self) -> None:
        """Removes ALL nodes and relationships for this graph_id."""
        query = """MATCH (n:Node {graph_id: $graph_id}) DETACH DELETE n"""
        with self._get_session() as session:
            session.execute_write(lambda tx: tx.run(query, graph_id=self.graph_id))

    def _get_session(self):
        """Returns driver session"""
        if self.database:
            return self.driver.session(database=self.database)
        return self.driver.session()

    def close(self):
        """Explicitly close the driver"""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def create_graph(
        self,
        vertices_data: List[dict],
        edges_data: List[Tuple[Tuple[int, int], EdgeType]],
        inputs: Optional[List[int]] = None,
        outputs: Optional[List[int]] = None,
    ) -> List[VT]:
        """Creates a graph with given vertices and edges"""
        if not vertices_data:
            return []
        # Anna nodeille ID:t
        vertices = list(range(self._vindex, self._vindex + len(vertices_data)))

        # Valmistellaan nodejen luominen
        all_vertices = []
        for v_id, data in zip(vertices, vertices_data):
            ty = data.get("ty", VertexType.BOUNDARY)
            phase = data.get("phase")
            if phase is not None:
                try:
                    phase = phase % 2
                except Exception:
                    pass
            phase_str = self._phase_to_str(phase) if phase is not None else "0"

            all_vertices.append(
                {
                    "id": v_id,
                    "t": ty.value,
                    "phase": phase_str,
                    "qubit": data.get("qubit", -1),
                    "row": data.get("row", -1),
                }
            )

        # Valmistellaan relationshippien luominen. Indeksit lopulta muuttuu edgejen ID:ksi.
        edge_ids = [self.num_edges() + x for x in range(len(edges_data))]
        if edges_data:
            #Edgejen id:t tallennetaan nyt aina pienemmästä vertex id:stä suurempaan. Tälleen voidaan pitää edgejen id:t järjestyksessä ja relationshippien suunta pysyy aina samana
            #Ei siis pitäisi ilmestyä enää edgejä, jotka kulkee: src --> tgt ja vielä uusi edge, joka tgt --> src.
            all_edges = [
                {"s": min(vertices[x[0][0]], vertices[x[0][1]]),
                 "t": max(vertices[x[0][0]], vertices[x[0][1]]), 
                 "et": x[1].value}
                for x in edges_data
            ]
            for edge, edge_id in zip(all_edges, edge_ids):
                edge["id"] = edge_id
        else:
            all_edges = []
        # Valmistellaan input ja output nodejen ID:T
        input_ids = [vertices[i] for i in inputs] if inputs else []
        output_ids = [vertices[i] for i in outputs] if outputs else []

        with self._get_session() as session:

            def create_full_graph(tx):
                # Luodaan kaikki nodet
                tx.run(
                    """
                    UNWIND $vertices AS v
                    CREATE (n:Node {
                        graph_id: $graph_id,
                        id: v.id,
                        t: v.t,
                        phase: v.phase,
                        qubit: v.qubit,
                        row: v.row
                    })
                """,
                    graph_id=self.graph_id,
                    vertices=all_vertices,
                )

                # Luodaan kaikki relationshipit nodeille
                if all_edges:
                    tx.run(
                        """
                        UNWIND $edges AS e
                        MATCH (n1:Node {graph_id: $graph_id, id: e.s})
                        MATCH (n2:Node {graph_id: $graph_id, id: e.t})
                        CREATE (n1)-[:Wire {t: e.et, id: e.id}]->(n2)
                    """,
                        graph_id=self.graph_id,
                        edges=all_edges,
                    )

                # Merkitään input nodet
                if input_ids:
                    tx.run(
                        """
                        UNWIND $ids AS vid
                        MATCH (n:Node {graph_id: $graph_id, id: vid})
                        SET n:Input
                    """,
                        graph_id=self.graph_id,
                        ids=input_ids,
                    )

                # Merkitään output nodet
                if output_ids:
                    tx.run(
                        """
                        UNWIND $ids AS vid
                        MATCH (n:Node {graph_id: $graph_id, id: vid})
                        SET n:Output
                    """,
                        graph_id=self.graph_id,
                        ids=output_ids,
                    )

            session.execute_write(create_full_graph)

        # Päivitetään indeksit ja input sekä output tuplet
        self._vindex += len(vertices_data)
        self._inputs = tuple(input_ids)
        self._outputs = tuple(output_ids)

        return vertices

    def add_edges(
        self,
        edge_pairs: Iterable[tuple[int, int]],
        edgetype: EdgeType = EdgeType.SIMPLE,
        *,
        edge_data: Optional[Iterable[EdgeType]] = None,
    ) -> None:
        """
        Adds multiple edges at once.
        """
        edges_list = list(edge_pairs)
        if not edges_list:
            return

        if edge_data is None:
            data_list = [edgetype] * len(edges_list)
        else:
            data_list = list(edge_data)
            if len(data_list) != len(edges_list):
                raise ValueError("edge_data must have same length as edge_pairs")

        existing = set(self.edges())
        edges = []
        edge_data = []
        for e, et in zip(edges_list, data_list):
            s, t = upair(*e)
            if s == t:
                if et == EdgeType.HADAMARD:
                    self.add_to_phase(s, 1)
                continue

            if (s, t) in existing:
                self.set_edge_type(e, et)
            else:
                edges.append(e)
                edge_data.append(et)

        if not edges:
            return
        n = self.num_edges()
        ids = [i + n for i in range(len(edges))]
        #Edgejen id:t tallennetaan nyt aina pienemmästä vertex id:stä suurempaan. Tälleen voidaan pitää edgejen id:t järjestyksessä ja relationshippien suunta pysyy aina samana
        #Ei siis pitäisi ilmestyä enää edgejä, jotka kulkee: src --> tgt ja vielä uusi edge, joka tgt --> src.
        edges_payload = [
            {"s": min(s, t), "t": max(s, t), "et": et.value, "id": eid}
            for (s, t), et, eid in zip(edges, edge_data, ids)
        ]

        query = """
        UNWIND $edges AS e
        MATCH (n1:Node {graph_id: $graph_id, id: e.s})
        MATCH (n2:Node {graph_id: $graph_id, id: e.t})
        MERGE (n1)-[r:Wire]->(n2)
        ON CREATE SET r.t = e.et, r.id = e.id
        ON MATCH SET r.t = e.et
        """

        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(query, graph_id=self.graph_id, edges=edges_payload)
            )

    def depth(self) -> int:
        # gets the maximum depth based on graph id.
        # if unsure / fails, it returns -1.
        query = """
        MATCH (n:Node {graph_id: $graph_id})
        WHERE n.row IS NOT NULL AND n.row >= 0
        RETURN coalesce(max(n.row), -1) AS maxr
        """
        with self._get_session() as session:
            rec = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id).single()
            )
            self._maxr = int(rec["maxr"]) if rec and rec["maxr"] is not None else -1
            return self._maxr

    def _phase_to_str(self, phase) -> str:
        if phase is None:
            return "0"
        return str(phase)

    def vindex(self) -> int:
        """returns private variable _vindex (int)"""
        return self._vindex

    def num_vertices(self):
        query = "MATCH (n:Node {graph_id: $graph_id}) RETURN n.id as id"
        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id).data()
            )
        ids = [r['id'] for r in result]
        return len(ids)

    def remove_vertices(self, vertices):
        """Removes the specified vertices from the graph."""
        if not vertices:
            return

        vertex_list = list(vertices)

        with self._get_session() as session:

            def delete_vertices(tx):
                # Delete all relationships connected to these vertices, then delete the vertices
                tx.run(
                    """
                    UNWIND $vertex_ids AS vid
                    MATCH (n:Node {graph_id: $graph_id, id: vid})
                    DETACH DELETE n
                    """,
                    graph_id=self.graph_id,
                    vertex_ids=vertex_list,
                )

            session.execute_write(delete_vertices)

        # Update inputs and outputs to remove deleted vertices
        self._inputs = tuple(v for v in self._inputs if v not in vertex_list)
        self._outputs = tuple(v for v in self._outputs if v not in vertex_list)

    def remove_isolated_vertices(self) -> None:
        """Deletes all vertices and vertex pairs that are not connected to any other vertex.

        Mirrors BaseGraph.remove_isolated_vertices semantics:
          - Isolated boundary vertex => TypeError
          - Isolated Z/X => absorbed into scalar via add_node(phase)
          - Isolated H_BOX => absorbed into scalar via add_phase(phase)
          - Degree-1 non-boundary vertex whose unique neighbor also has degree-1
            and neither is boundary
            => remove both and update scalar depending on types and edge type.
        """
        rem: List[VT] = []

        # IMPORTANT: vertices() hits the DB, but we want a snapshot because we’ll delete.
        for v in list(self.vertices()):
            d = self.vertex_degree(v)

            # Completely isolated vertex
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

            # A dangling component of size 2: v--w and nothing else
            if d == 1:
                if v in rem:
                    continue
                if self.type(v) == VertexType.BOUNDARY:
                    continue

                ws = list(self.neighbors(v))
                if not ws:
                    continue
                w = ws[0]

                # Neighbor has other neighbors => not isolated pair
                if len(list(self.neighbors(w))) > 1:
                    continue
                if self.type(w) == VertexType.BOUNDARY:
                    continue

                # Now v and w are only connected to each other
                rem.append(v)
                rem.append(w)

                et = self.edge_type(self.edge(v, w))
                t1 = self.type(v)
                t2 = self.type(w)

                # 1-ary H-box behaves like a Z-spider here
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

        # Perform deletions in one go (Neo4j DETACH DELETE handles incident relationships)
        self.remove_vertices(rem)

    def num_edges(
        self,
        s: Optional[VT] = None,
        t: Optional[VT] = None,
        et: Optional[EdgeType] = None,
    ) -> int:
        """Returns the number of edges in the graph.

        Jos source ja target nodet on annettu erikseen, laskee niiden väliset kaaret.
        Jos kaaren tyyppi on annettu, laskee vain sen tyyppiset kaaret
        """
        if s is not None and t is not None:
            #Kaarien laskeminen kahden noden välillä myös pienemmästä id:stä suurempaan
            s, t = (s, t) if s <= t else (t, s)
            if et is not None:
                query = """
                MATCH (n1:Node {graph_id: $graph_id, id: $s})-[r:Wire {t: $et}]->(n2:Node {graph_id: $graph_id, id: $t})
                RETURN count(r) as count
                """
                params = {"graph_id": self.graph_id, "s": s, "t": t, "et": et.value}
            else:
                query = """
                MATCH (n1:Node {graph_id: $graph_id, id: $s})-[r:Wire]->(n2:Node {graph_id: $graph_id, id: $t})
                RETURN count(r) as count
                """
                params = {"graph_id": self.graph_id, "s": s, "t": t}

            with self._get_session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, **params).single()
                )
            count = result["count"] if result else 0
            return count
        if s is not None:
            # Count edges incident to a specific vertex
            return self.vertex_degree(s)
        else:
            # Count all edges
            query = """
            MATCH (:Node {graph_id: $graph_id})-[r:Wire]->(:Node {graph_id: $graph_id})
            RETURN count(r) as count
            """
            with self._get_session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, graph_id=self.graph_id).single()
                )
            return result["count"] if result else 0

    def add_edge(
        self, edge_pair: Tuple[VT, VT], edgetype: EdgeType = EdgeType.SIMPLE
    ) -> ET:
        """Adds a single edge of the given type and return its id.

        Nyt myös seuraten paremmin ZX-calculuksen sääntöjä
        """
        s, t = edge_pair[0], edge_pair[1]
        t1 = self.type(s)
        t2 = self.type(t)

        #Pidetään huoli, että self-looppeja ei voida lisätä
        if s == t:
            if not vertex_is_zx_like(t1) or not vertex_is_zx_like(t2):
                raise ValueError(
                    "Unexpected vertex type, it should be either z or x "
                    "trying to add a selp-loop"
                )
            if edgetype == EdgeType.SIMPLE:
                return upair(s, t)
            elif edgetype == EdgeType.HADAMARD:
                self.add_to_phase(s, 1)
                return upair(s, t)
            else:
                raise ValueError("The edge you are adding is not an appropriate type")

        #Tarkastetaan jos edge on jo olemassa
        if not self.connected(s, t):
            #Edgeä ei ollut olemassa, joten lisätään edge ja pidetään taas huoli, että edge lisätään pienemmästä id:stä suurempaan.
            src, tgt = upair(s, t)
            edge_id = self.num_edges()

            query = """
            MATCH (n1:Node {graph_id: $graph_id, id: $s})
            MATCH (n2:Node {graph_id: $graph_id, id: $t})
            CREATE (n1)-[:Wire {t: $et, id: $eid}]->(n2)
            """
            with self._get_session() as session:
                session.execute_write(
                    lambda tx: tx.run(
                        query,
                        graph_id=self.graph_id,
                        s=src,
                        t=tgt,
                        et=edgetype.value,
                        eid=edge_id,
                    )
                )
        else:
            #Jos edge oli jo olemassa, käytetään ZX-calculuksen rewrite sääntöjä edgejen yhdistämiseen
            if vertex_is_zx_like(t1) and vertex_is_zx_like(t2):
                et1 = self.edge_type(self.edge(s, t))

                #Määritetään vertexien tyyppien perustella, mitä sääntöjä sovelletaan mihinkin
                if vertex_is_z_like(t1) == vertex_is_z_like(t2):  # same colour
                    fuse, hopf = (EdgeType.SIMPLE, EdgeType.HADAMARD)
                else:
                    fuse, hopf = (EdgeType.HADAMARD, EdgeType.SIMPLE)

                #Käsittele parellel edgejä kaikilla eri fuse/hopf sääntöjäen yhdistelmillä
                if edgetype == fuse and et1 == fuse:
                    pass  #Tämän edgen lisääminen aiheuttaisi parallel edgen, jolla on sama tyyppi, joten mitään ei tehdä
                elif (edgetype == fuse and et1 == hopf) or (
                    edgetype == hopf and et1 == fuse
                ):
                    #Varmistetaan, että viimeinen edge on tyypiltään fuse
                    self.set_edge_type(self.edge(s, t), fuse)
                    #Lisää pii phase yhteen naapureista
                    if t1 == VertexType.Z_BOX:
                        set_z_box_label(self, s, get_z_box_label(self, s) * -1)
                    else:
                        self.add_to_phase(s, 1)
                    self.scalar.add_power(-1)
                elif edgetype == hopf and et1 == hopf:
                    #Poistetaan edge, joka on tyypiltään hopf, joka oli myös jo olemassa, vähennetään phasesta mod 2
                    self.remove_edge(self.edge(s, t))
                    self.scalar.add_power(-2)
                else:
                    raise ValueError(f"Got unexpected edge types: {t1}, {t2}")
            else:
                if (vertex_is_z_like(t1) and t2 == VertexType.H_BOX) or (
                    vertex_is_z_like(t2) and t1 == VertexType.H_BOX
                ):
                    if edgetype == EdgeType.SIMPLE:
                        return upair(s, t)
                raise ValueError(
                    f"Attempted to add unreducible parallel edge {edge_pair}, "
                    f"types: {t1}, {t2}"
                )

        return upair(s, t)

    def remove_edges(self, edges: List[ET]) -> None:
        """Removes relationships from the graph"""
        if not edges:
            return

        edges_payload = [{"s": s, "t": t} for s, t in edges]

        query = """
        UNWIND $edges AS e
        MATCH (n1:Node {graph_id: $graph_id, id: e.s})-[r:Wire]-(n2:Node {graph_id: $graph_id, id: e.t})
        DELETE r
        """

        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(query, graph_id=self.graph_id, edges=edges_payload)
            )

    def vertices(self) -> Iterable[VT]:
        """Iterator over all the vertices."""

        query = """MATCH (n:Node {graph_id: $graph_id}) RETURN n.id AS id"""
        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id).data()
            )
        return [r["id"] for r in result]

    def edges(self, s: Optional[VT] = None, t: Optional[VT] = None) -> Iterable[ET]:
        """Iterator that returns all the edges in the graph,
        or all the edges connecting the pair of vertices.
        Output type depends on implementation in backend."""

        if s is not None and t is not None:
            vertices_payload = [{"s": s, "t": t}]

            query = """
            UNWIND $vertices as v
            MATCH (n1:Node {graph_id: $graph_id, id: v.s})-[r:Wire]-(n2:Node {graph_id: $graph_id, id: v.t})
            RETURN startNode(r).id AS src, endNode(r).id AS tgt"""
            with self._get_session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(
                        query, graph_id=self.graph_id, vertices=vertices_payload
                    ).data()
                )
            return [(item["src"], item["tgt"]) for item in result]

        query = "MATCH (n1:Node {graph_id: $graph_id})-[r:Wire]->(n2:Node {graph_id: $graph_id})"
        query += " WHERE n1.id <= n2.id"
        query += " RETURN n1.id, n2.id"
        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id).data()
            )
        return [(item["n1.id"], item["n2.id"]) for item in result]

    def edge_st(self, edge: ET) -> Tuple[VT, VT]:
        """Returns a tuple of source/target of the given edge."""
        return edge

    def incident_edges(self, vertex: VT) -> Sequence[ET]:
        """Returns all neighboring edges of the given vertex."""

        query = """
        MATCH (n:Node {graph_id: $graph_id, id: $vertex})-[r:Wire]-(m:Node {graph_id: $graph_id})
        RETURN startNode(r).id AS src, endNode(r).id AS tgt
        """

        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id, vertex=vertex).data()
            )

        return [(r["src"], r["tgt"]) for r in result]

    def edge_type(self, e: ET) -> EdgeType:
        """Returns the type of the given edge:
        ``EdgeType.SIMPLE`` if it is regular, ``EdgeType.HADAMARD`` if it is a Hadamard edge
        Raises KeyError if the edge is not in the graph.
        """

        query = """MATCH
        (n1:Node {graph_id: $graph_id, id: $node1})
        -[r:Wire]-(n2:Node {graph_id: $graph_id, id: $node2})
        RETURN r.t"""
        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(
                    query, graph_id=self.graph_id, node1=e[0], node2=e[1]
                ).data()
            )

        if len(result) <= 0:
            raise KeyError(f"{e} has no edge type")

        return EdgeType(result[0]["r.t"])

    def set_edge_type(self, e: ET, t: EdgeType) -> None:
        """Sets the type of the given edge."""
        query = """MATCH
        (n1:Node {graph_id: $graph_id, id: $node1})
        -[r:Wire]-(n2:Node {graph_id: $graph_id, id: $node2})
        SET r.t = $type"""
        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    query, graph_id=self.graph_id, node1=e[0], node2=e[1], type=t.value
                )
            )

    def type(self, vertex: VT) -> VertexType:
        """Returns the type of the given vertex:
        VertexType.BOUNDARY if it is a boundary, VertexType.Z if it is a Z node,
        VertexType.X if it is a X node, VertexType.H_BOX if it is an H-box."""

        query = """MATCH (n:Node {graph_id: $graph_id, id: $id}) RETURN n.t"""
        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex).data()
            )
        if not result:
            raise KeyError(f"{vertex} has no type")

        return VertexType(result[0]["n.t"])

    def set_type(self, vertex: VT, t: VertexType) -> None:
        """Sets the type of the given vertex to t."""

        query = """MATCH (n:Node {graph_id: $graph_id, id: $id}) SET n.t = $type"""
        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex, type=t.value)
            )

    def phase(self, vertex: VT) -> FractionLike:
        """Returns the phase value of the given vertex."""
        query = """MATCH (n:Node {graph_id: $graph_id, id: $id}) RETURN n.phase"""
        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex).data()
            )
        if not result:
            return 0
        p = result[0]["n.phase"]
        if p is None:
            return 0
        try:
            return Fraction(p)
        except ValueError:
            try:
                return parse(p, lambda x: new_var(x, False))
            except Exception:
                return Fraction(0)

    def set_phase(self, vertex: VT, phase: FractionLike) -> None:
        """Sets the phase of the vertex to the given value."""
        try:
            phase = phase % 2
        except Exception:
            pass
        query = """MATCH (n:Node {graph_id: $graph_id, id: $id}) SET n.phase = $phase"""
        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    query,
                    graph_id=self.graph_id,
                    id=vertex,
                    phase=self._phase_to_str(phase),
                )
            )

    def qubit(self, vertex: VT) -> FloatInt:
        """Returns the qubit index associated to the vertex.
        If no index has been set, returns -1."""
        query = """ MATCH (n:Node {graph_id: $graph_id, id: $id}) RETURN n.qubit AS qubit
        """
        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex).single())
        #Muutetaan .datasta .singleksi, kun tarkastellaan vain yhtä vertexiä kuitenkin kerralla
        return result["qubit"] if result else -1

    def set_qubit(self, vertex: VT, q: FloatInt) -> None:
        """Sets the qubit index associated to the vertex."""
        query = (
            """ MATCH (n:Node {graph_id: $graph_id, id: $id}) SET n.qubit = $qubit""")

        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    query,
                    graph_id=self.graph_id,
                    id=vertex,
                    qubit=q))

    def row(self, vertex: VT) -> FloatInt:
        """Palauttaa sen rivin jolla verteksi on.
        Jos ei ole asetettu, palauttaa -1 -1."""
        query = "MATCH (n:Node {graph_id: $graph_id, id: $id}) RETURN n.row AS r"
        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex).single()
            )
        #Palautetaan taas .single koska tarkastellaan vain yhtä vertexiä kerralla
        return result["r"] if result and result["r"] is not None else -1

    def set_row(self, vertex: VT, r: FloatInt) -> None:
        """Asettaa rivin verteksille."""
        query = """
        MATCH (n:Node {graph_id: $graph_id, id: $id})
        SET n.row = $r
        """
        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex, r=r)
            )

    def clear_vdata(self, vertex: VT) -> None:
        """Removes all vdata associated to a vertex"""
        query = """MATCH (n:Node {graph_id: $graph_id, id: $id})
        SET n = {id: $id, t: n.t, phase: n.phase, qubit: n.qubit,
        row: n.row, graph_id: $graph_id}"""

        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex)
            )

    def vdata_keys(self, vertex: VT) -> Sequence[str]:
        """Returns an iterable of the vertex data key names.
        Used e.g. in making a copy of the graph in a backend-independent way."""

        query = (
            """ MATCH(n:Node {graph_id: $graph_id, id: $id}) RETURN keys(n) AS keys"""
        )
        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex).single()
            )
        #Muutetaan taas .singleksi, koska vain yksi vertex tarkastelussa
        return result["keys"]

    def vdata(self, vertex: VT, key: str, default: Any = None) -> Any:
        """Returns the data value of the given vertex associated to the key.
        If this key has no value associated with it, it returns the default value."""
        query = (
            """MATCH (n:Node {graph_id: $graph_id, id: $id}) RETURN n[$key] as value"""
        )

        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(
                    query, graph_id=self.graph_id, id=vertex, key=key
                ).data()
            )
        return result[0]["value"] if result and result[0]["value"] is not None else default

    def set_vdata(self, vertex: VT, key: str, val: Any) -> None:
        """Sets the vertex data associated to key to val."""
        query = """ MATCH (n:Node {graph_id: $graph_id, id: $id}) SET n[$key] = $val"""

        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    query, graph_id=self.graph_id, id=vertex, key=key, val=val
                )
            )

    def clear_edata(self, edge: ET) -> None:
        """Removes all edata associated to an edge"""

        query = """MATCH (n1:Node {graph_id: $graph_id, id: $node1})
        -[r:Wire]->(n2:Node {graph_id: $graph_id, id: $node2})
        SET r = {id: r.id, t: r.t}"""
        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    query, graph_id=self.graph_id, node1=edge[0], node2=edge[1]
                )
            )

    def edata_keys(self, edge: ET) -> Sequence[str]:
        """Returns an iterable of the edge data key names."""

        query = """
        MATCH (n1:Node {graph_id: $graph_id, id: $node1}) -[r:Wire]->(n2:Node {graph_id: $graph_id, id: $node2})
        RETURN keys(r) AS propertyKey"""

        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(
                    query, graph_id=self.graph_id, node1=edge[0], node2=edge[1]
                ).data()
            )

        if len(result) > 1:
            raise ValueError(
                f"Expected single Wire between {edge}, found {len(result)}"
            )
        return result[0]["propertyKey"] if result else []

    def edata(self, edge: ET, key: str, default: Any = None) -> Any:
        """Returns the data value of the given edge associated to the key.
        If this key has no value associated with it, it returns the default value."""
        query = """
        MATCH (n1:Node {graph_id: $graph_id, id: $node1}) -[r:Wire]->(n2:Node {graph_id: $graph_id, id: $node2})
        RETURN r[$key] AS value"""

        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(
                    query, graph_id=self.graph_id, node1=edge[0], node2=edge[1], key=key
                ).single()
            )
        #Muutetaan täälläkin .singleksi
        return result["value"] if result and result["value"] is not None else default

    def set_edata(self, edge: ET, key: str, val: Any) -> None:
        """Sets the edge data associated to key to val."""

        query = """
        MATCH (n1:Node {graph_id: $graph_id, id: $node1}) -[r:Wire]->(n2:Node {graph_id: $graph_id, id: $node2})
        SET r[$key] = $val"""

        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    query,
                    graph_id=self.graph_id,
                    node1=edge[0],
                    node2=edge[1],
                    key=key,
                    val=val,
                )
            )

    def run_cypher_rewrite(
        self,
        rule_name: str,
        variant_id: Optional[str] = None,
        query_config: Optional[Mapping[str, str]] = None,
        measure_time: bool = False,
    ) -> Tuple[Optional[Mapping[str, Any]], Optional[float]]:
        """Run a named Cypher rewrite from neo4j_queries with this graph's session and graph_id.
        See neo4j_rewrite_runner for rule names and variant selection (env/config)."""
        return run_rewrite(
            self._get_session,
            self.graph_id,
            rule_name,
            variant_id=variant_id,
            query_config=dict(query_config) if query_config else None,
            measure_time=measure_time,
        )

    # }}}

    # OPTIONAL OVERRIDES{{{

    # These only need to be overridden if the backend will be used with hybrid classical/quantum
    # methods.
    def is_ground(self, vertex: VT) -> bool:
        """Returns a boolean indicating if the vertex is connected to a ground."""
        return False

    def grounds(self) -> Set[VT]:
        """Returns the set of vertices connected to a ground."""
        return set(v for v in self.vertices() if self.is_ground(v))

    def set_ground(self, vertex: VT, flag: bool = True) -> None:
        """Connect or disconnect the vertex to a ground."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)

    def is_hybrid(self) -> bool:
        """Returns whether this is a hybrid quantum-classical graph,
        i.e. a graph with ground generators."""
        return bool(self.grounds())

    # Override and set to true if the backend supports parallel edges
    def multigraph(self) -> bool:
        return False

    # Backends may wish to override these methods to implement them more efficiently

    # These methods return mappings from vertices to various pieces of data. If the backend
    # stores these e.g. as Python dicts, just return the relevant dicts.
    def phases(self) -> Mapping[VT, FractionLike]:
        """Returns a mapping of vertices to their phase values."""
        return {v: self.phase(v) for v in self.vertices()}

    def types(self) -> Mapping[VT, VertexType]:
        """Returns a mapping of vertices to their types."""
        return {v: self.type(v) for v in self.vertices()}

    def qubits(self) -> Mapping[VT, FloatInt]:
        """Returns a mapping of vertices to their qubit index."""
        return {v: self.qubit(v) for v in self.vertices()}

    def rows(self) -> Mapping[VT, FloatInt]:
        """Returns a mapping of vertices to their row index."""
        return {v: self.row(v) for v in self.vertices()}

    def edge(self, s: VT, t: VT, et: Optional[EdgeType] = None) -> ET:
        """Returns the name of the first edge with the given source/target and type.
        Behaviour is undefined if the vertices are not connected."""
        for e in self.incident_edges(s):
            if t in self.edge_st(e):
                if et is None or et == self.edge_type(e):
                    return e
        if et is not None:
            raise ValueError(f"No edge of type {et} between {s} and {t}")

        raise ValueError(f"No edge between {s} and {t}")

    def connected(self, v1: VT, v2: VT) -> bool:
        """Returns whether vertices v1 and v2 share an edge."""
        query = """MATCH (n:Node {graph_id: $graph_id, id: $vid1})-[r:Wire]-(n2:Node {graph_id: $graph_id, id: $vid2}) RETURN r"""
        with self._get_session() as session:
            r = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id, vid1=v1, vid2=v2).data()
            )
        return len(r) != 0

    def add_vertex(
        self,
        ty: VertexType = VertexType.BOUNDARY,
        qubit: FloatInt = -1,
        row: FloatInt = -1,
        phase: Optional[FractionLike] = None,
        ground: bool = False,
        index: Optional[VT] = None,
    ) -> VT:
        """Add a single vertex to the graph and return its index.
        The optional parameters allow you to respectively set
        the type, qubit index, row index and phase of the vertex."""
        if index is not None:
            self.add_vertex_indexed(index)
            v = index
        else:
            v = self.add_vertices(1)[0]
        self.set_type(v, ty)
        if phase is None:
            if ty == VertexType.H_BOX:
                phase = 1
            else:
                phase = 0
        self.set_qubit(v, qubit)
        self.set_row(v, row)
        if phase:
            self.set_phase(v, phase)
        if ground:
            self.set_ground(v, True)
        if self.track_phases:
            self.max_phase_index += 1
            self.phase_index[v] = self.max_phase_index
            self.phase_mult[self.max_phase_index] = 1
        return v

    def add_vertex_indexed(self, v: VT) -> None:
        """Adds a vertex that is guaranteed to have the chosen index (i.e. 'name').
        If the index isn't available, raises a ValueError.
        This method is used in the editor and ZXLive to support undo,
        which requires vertices to preserve their index.
        """
        # 1) Check availability
        q_exists = """
        MATCH (n:Node {graph_id: $graph_id, id: $id})
        RETURN count(n) AS c
        """
        with self._get_session() as session:
            rec = session.execute_read(
                lambda tx: tx.run(q_exists, graph_id=self.graph_id, id=v).single()
            )
            if rec and int(rec["c"]) > 0:
                raise ValueError("Vertex with this index already exists")

        # 2) Create with defaults (same defaults as add_vertices)
        q_create = """
        CREATE (n:Node {
            graph_id: $graph_id,
            id: $id,
            t: $t,
            phase: $phase,
            qubit: $qubit,
            row: $row
        })
        """
        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    q_create,
                    graph_id=self.graph_id,
                    id=v,
                    t=VertexType.BOUNDARY.value,
                    phase="0",
                    qubit=-1,
                    row=-1,
                )
            )

        # 3) Maintain vindex contract
        if v >= self._vindex:
            self._vindex = v + 1

    def add_vertices(self, amount: int) -> List[VT]:
        """Adds ``amount`` number of vertices and returns a list containing their IDs

        Neo4j nodes are stored as (:Node {graph_id, id, t, phase, qubit, row})

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

        vertex_ids: List[VT] = list(range(self._vindex, self._vindex + amount))
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

        query = """
        UNWIND $vertices AS v
        CREATE (n:Node {
            graph_id: $graph_id,
            id: v.id,
            t: v.t,
            phase: v.phase,
            qubit: v.qubit,
            row: v.row
        })
        """

        with self._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(query, graph_id=self.graph_id, vertices=payload)
            )

        self._vindex += amount
        return vertex_ids

    def set_outputs(self, outputs: Tuple[VT, ...]):
        """Sets the outputs of the graph.

        Behaviour:
        - Updates the in-memory outputs tuple (`self._outputs`).
        - Synchronizes Neo4j labels:
            * removes :Output from all nodes of this graph_id
            * sets :Output on nodes whose ids are in `outputs`
        """
        self._outputs = tuple(outputs)
        ids: List[int] = list(self._outputs)

        q_clear = """
        MATCH (n:Output {graph_id: $graph_id})
        REMOVE n:Output
        """
        q_set = """
        UNWIND $ids AS vid
        MATCH (n:Node {graph_id: $graph_id, id: vid})
        SET n:Output
        """

        with self._get_session() as session:

            def _tx(tx):
                tx.run(q_clear, graph_id=self.graph_id)
                tx.run(q_set, graph_id=self.graph_id, ids=ids)

            session.execute_write(_tx)

    def outputs(self) -> Tuple[VT, ...]:
        """Gets the outputs of the graph.

        Behaviour:
        - Returns the in-memory outputs tuple (`self._outputs`) if it is non-empty.
        - Otherwise attempts to read outputs from Neo4j labels (:Output) for this graph_id,
          returns them ordered by vertex id.
        - If neither exists, returns an empty tuple.
        """
        if getattr(self, "_outputs", None):
            return self._outputs

        query = """
        MATCH (n:Output {graph_id: $graph_id})
        RETURN n.id AS id
        ORDER BY id
        """
        with self._get_session() as session:
            rows = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id).data()
            )

        ids: List[int] = [int(r["id"]) for r in rows]
        self._outputs = tuple(ids)
        return self._outputs

    def set_inputs(self, inputs: Tuple[VT, ...]):
        """Sets the inputs of the graph.

        Behaviour:
        - Updates the in-memory inputs tuple (`self._inputs`).
        - Synchronizes Neo4j labels:
            * removes :Input from all nodes of this graph_id
            * sets :Input on nodes whose ids are in `inputs`
        """
        self._inputs = tuple(inputs)
        ids: List[int] = list(self._inputs)

        q_clear = """
        MATCH (n:Input {graph_id: $graph_id})
        REMOVE n:Input
        """
        q_set = """
        UNWIND $ids AS vid
        MATCH (n:Node {graph_id: $graph_id, id: vid})
        SET n:Input
        """

        with self._get_session() as session:

            def _tx(tx):
                tx.run(q_clear, graph_id=self.graph_id)
                tx.run(q_set, graph_id=self.graph_id, ids=ids)

            session.execute_write(_tx)

    def remove_vertex(self, vertex: VT) -> None:
        """Removes the given vertex from the graph."""
        self.remove_vertices([vertex])

    def remove_edge(self, edge: ET) -> None:
        """Removes the given edge from the graph."""
        self.remove_edges([edge])

    def add_to_phase(self, vertex: VT, phase: FractionLike) -> None:
        """Add the given phase to the phase value of the given vertex."""
        self.set_phase(vertex, self.phase(vertex) + phase)

    def num_inputs(self) -> int:
        """Gets the number of inputs of the graph."""
        return len(self.inputs())

    def num_outputs(self) -> int:
        """Gets the number of outputs of the graph."""
        return len(self.outputs())

    def set_position(self, vertex: VT, q: FloatInt, r: FloatInt):
        """Set both the qubit index and row index of the vertex."""
        self.set_qubit(vertex, q)
        self.set_row(vertex, r)

    def neighbors(self, vertex: VT) -> Sequence[VT]:
        """Returns all neighboring vertices of the given vertex."""
        vs: Set[VT] = set()
        for e in self.incident_edges(vertex):
            s, t = self.edge_st(e)
            vs.add(s if t == vertex else t)
        return list(vs)

    def vertex_degree(self, vertex: VT) -> int:
        """Returns the degree of the given vertex."""
        return len(self.incident_edges(vertex))

    def edge_s(self, edge: ET) -> VT:
        """Returns the source of the given edge."""
        return self.edge_st(edge)[0]

    def edge_t(self, edge: ET) -> VT:
        """Returns the target of the given edge."""
        return self.edge_st(edge)[1]

    def vertex_set(self) -> Set[VT]:
        """Returns the vertices of the graph as a Python set.
        Should be overloaded if the backend supplies a cheaper version than this."""
        return set(self.vertices())

    def edge_set(self) -> Set[ET]:
        """Returns the edges of the graph as a Python set.
        Should be overloaded if the backend supplies a cheaper version than this.
        Note this ignores parallel edges."""
        return set(self.edges())

    def inputs(self) -> Tuple[VT, ...]:
        """Gets the inputs of the graph.

        Behaviour:
        - Returns the in-memory inputs tuple (`self._inputs`) if it is non-empty.
        - Otherwise attempts to read inputs from Neo4j labels (:Input) for this graph_id,
          returns them ordered by vertex id.
        - If neither exists, returns an empty tuple.
        """
        if getattr(self, "_inputs", None):
            return self._inputs

        query = """
        MATCH (n:Input {graph_id: $graph_id})
        RETURN n.id AS id
        ORDER BY id
        """
        with self._get_session() as session:
            rows = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id).data()
            )

        ids: List[int] = [int(r["id"]) for r in rows]
        self._inputs = tuple(ids)
        return self._inputs

    def copy(
        self, adjoint: bool = False, backend: Optional[str] = None
    ) -> "BaseGraph[VT, ET]":
        """Tällä metodilla saa luotua kopion neo4j graafista.
        Käytetään BaseGraph copy metodia.
        """
        # Jos halutaan graafista kopio mahdollisesti johonkin toisen backendiin
        # voi käyttää perus copy metodia
        if adjoint or (backend is not None and backend != "neo4j"):
            return super().copy(adjoint=adjoint, backend=backend)

        #Kutsutaan kloonaus metodia.
        return self.clone()

    def clone(self) -> "GraphNeo4j":
        """Return an identical copy of the graph without relabeling vertices/edges.

        For the Neo4j backend, this means copying all (:Node) vertices and (:Wire)
        relationships belonging to this instance's ``graph_id`` into a fresh
        ``graph_id`` namespace, preserving the ``id`` fields and all properties.
        """


        # Fresh namespace so the copy won't clash with existing data.
        new_graph_id = f"{self.graph_id}_clone_{uuid.uuid4().hex}"
        cpy = GraphNeo4j(
            uri=self.uri,
            user=self.user,
            password=self.password,
            graph_id=new_graph_id,
            database=self.database,
        )

        # Copy BaseGraph-level state that is not stored in the DB.
        cpy.scalar = self.scalar.copy()
        cpy.track_phases = self.track_phases
        cpy.phase_index = self.phase_index.copy()
        cpy.phase_master = self.phase_master
        cpy.phase_mult = self.phase_mult.copy()
        cpy.max_phase_index = self.max_phase_index
        cpy.merge_vdata = self.merge_vdata

        # Preserve backend bookkeeping.
        cpy._vindex = self._vindex
        cpy._maxr = self._maxr

        # Snapshot the current graph from Neo4j.
        q_nodes = """
        MATCH (n:Node {graph_id: $graph_id})
        RETURN n.id AS id, properties(n) AS props, labels(n) AS labels
        ORDER BY id
        """

        q_edges = """
        MATCH (n1:Node {graph_id: $graph_id})-[r:Wire]->(n2:Node {graph_id: $graph_id})
        RETURN n1.id AS s, n2.id AS t, properties(r) AS props
        """

        with self._get_session() as session:
            nodes_rows = session.execute_read(
                lambda tx: tx.run(q_nodes, graph_id=self.graph_id).data()
            )

            # Empty graph: just copy scalar/state.
            if not nodes_rows:
                cpy._inputs = tuple(self.inputs())
                cpy._outputs = tuple(self.outputs())
                return cpy

            edges_rows = session.execute_read(
                lambda tx: tx.run(q_edges, graph_id=self.graph_id).data()
            )

            node_payload = []
            label_inputs = []
            label_outputs = []

            for row in nodes_rows:
                props = dict(row.get("props") or {})
                props["graph_id"] = new_graph_id  # move to new namespace
                node_payload.append(props)

                labels = row.get("labels") or []
                if "Input" in labels:
                    label_inputs.append(int(props["id"]))
                if "Output" in labels:
                    label_outputs.append(int(props["id"]))

            # Preserve ordering if present in-memory; otherwise fall back to label-derived order.
            input_ids = list(self._inputs) if getattr(self, "_inputs", None) else []
            output_ids = list(self._outputs) if getattr(self, "_outputs", None) else []
            if not input_ids:
                input_ids = label_inputs
            if not output_ids:
                output_ids = label_outputs

            edges_payload = [
                {
                    "s": int(r["s"]),
                    "t": int(r["t"]),
                    "props": dict(r.get("props") or {}),
                }
                for r in (edges_rows or [])
            ]

            q_create_nodes = """
            UNWIND $nodes AS p
            CREATE (n:Node)
            SET n = p
            """

            q_create_edges = """
            UNWIND $edges AS e
            MATCH (s:Node {graph_id: $new_graph_id, id: e.s})
            MATCH (t:Node {graph_id: $new_graph_id, id: e.t})
            CREATE (s)-[r:Wire]->(t)
            SET r = e.props
            """

            q_set_inputs = """
            UNWIND $ids AS vid
            MATCH (n:Node {graph_id: $new_graph_id, id: vid})
            SET n:Input
            """

            q_set_outputs = """
            UNWIND $ids AS vid
            MATCH (n:Node {graph_id: $new_graph_id, id: vid})
            SET n:Output
            """

            def _write(tx):
                tx.run(q_create_nodes, nodes=node_payload)
                if edges_payload:
                    tx.run(
                        q_create_edges, new_graph_id=new_graph_id, edges=edges_payload
                    )
                if input_ids:
                    tx.run(q_set_inputs, new_graph_id=new_graph_id, ids=input_ids)
                if output_ids:
                    tx.run(q_set_outputs, new_graph_id=new_graph_id, ids=output_ids)

            session.execute_write(_write)

        # Sync in-memory IO.
        cpy._inputs = tuple(input_ids)
        cpy._outputs = tuple(output_ids)

        return cpy
