import os
from typing import List, Optional, Tuple

from dotenv import load_dotenv
from neo4j import GraphDatabase

from ..utils import EdgeType, VertexType
from .base import BaseGraph

load_dotenv()

VT = int
ET = Tuple[int, int]


class GraphNeo4j(BaseGraph[VT, ET]):
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

    def _get_session(self):
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
        if not vertices_data:
            return []

        # Anna nodeille ID:t
        vertices = list(range(self._vindex, self._vindex + len(vertices_data)))

        # Valmistellaan nodejen luominen
        all_vertices = []
        for v_id, data in zip(vertices, vertices_data):
            ty = data.get("ty", VertexType.BOUNDARY)
            phase = data.get("phase")
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

        # Valmistellaan relationshippien luominen. Indeksit lopulta muuttuu nodejen ID:eiksi
        all_edges = (
            [
                {"s": vertices[x[0][0]], "t": vertices[x[0][1]], "et": x[1].value}
                for x in edges_data
            ]
            if edges_data
            else []
        )

        # Valmistellaan input ja output nodejen ID:T
        input_ids = [vertices[i] for i in inputs] if inputs else []
        output_ids = [vertices[i] for i in outputs] if outputs else []

        graph_id = self.graph_id

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
                    graph_id=graph_id,
                    vertices=all_vertices,
                )

                # Luodaan kaikki relationshipit nodeille
                if all_edges:
                    tx.run(
                        """
                        UNWIND $edges AS e
                        MATCH (n1:Node {graph_id: $graph_id, id: e.s})
                        MATCH (n2:Node {graph_id: $graph_id, id: e.t})
                        CREATE (n1)-[:Wire {t: e.et}]->(n2)
                    """,
                        graph_id=graph_id,
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
                        graph_id=graph_id,
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
                        graph_id=graph_id,
                        ids=output_ids,
                    )

            session.execute_write(create_full_graph)

        # Päivitetään indeksit ja input sekä output tuplet
        self._vindex += len(vertices_data)
        self._inputs = tuple(input_ids)
        self._outputs = tuple(output_ids)

        return vertices

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
        return self.num_vertices()
    
    def num_vertices(self):
        query = "MATCH (n:Node {graph_id: $graph_id}) RETURN count(n) AS count"
        with self._get_session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, graph_id=self.graph_id).single()
            )
        return result["count"] if result else 0
