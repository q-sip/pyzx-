# tests/test_graph_neo4j/test_add_edges.py
import pytest
from neo4j import Session

from pyzx.utils import EdgeType, VertexType
from pyzx.graph.graph_neo4j import GraphNeo4j


class TestAddEdges:
    """
    Tests for the add_edges method. 
    Uses the 'neo4j_graph_e2e' fixture from conftest.py which handles
    connection, graph_id generation, and cleanup.
    """

    def test_add_edges_simple(self, neo4j_graph_e2e: GraphNeo4j):
        """
        Yksinkertaiset edget
        """
        g = neo4j_graph_e2e
        
        # 1. Setup: Create nodes using the existing create_graph method
        # We need nodes 0, 1, 2 to exist before adding edges to them.
        nodes = [
            {"id": 0, "ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"id": 1, "ty": VertexType.Z, "row": 1, "qubit": 0},
            {"id": 2, "ty": VertexType.X, "row": 1, "qubit": 1},
        ]
        g.create_graph(nodes, [])  # Initialize with 0 edges

        # 2. Action: Add edges using the method we are testing
        # Edge 0->1 and 1->2
        edges_to_add = [(0, 1), (1, 2)]
        g.add_edges(edges_to_add)

        # 3. Verification: Query Neo4j directly to confirm edges exist
        query = """
        MATCH (n:Node {graph_id: $gid})-[r:Wire]->(m:Node {graph_id: $gid})
        RETURN n.id as src, m.id as tgt, r.t as type
        """
        
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id).data()

        # We expect exactly 2 edges
        assert len(result) == 2
        
        # Verify specific connections
        edge_0_1 = next((r for r in result if r['src'] == 0 and r['tgt'] == 1), None)
        assert edge_0_1 is not None
        assert edge_0_1['type'] == EdgeType.SIMPLE.value

    def test_add_edges_with_types(self, neo4j_graph_e2e: GraphNeo4j):
        """
        Eri tyyppisten edgejen lisäys
        """
        g = neo4j_graph_e2e

        # 1. Setup
        nodes = [
            {"id": 0, "ty": VertexType.BOUNDARY},
            {"id": 1, "ty": VertexType.Z},
            {"id": 2, "ty": VertexType.X}
        ]
        g.create_graph(nodes, [])

        # 2. Action: Add edges with explicit types
        edges = [(0, 1), (1, 2)]
        # Make the first edge SIMPLE and the second HADAMARD
        edge_types = [EdgeType.SIMPLE, EdgeType.HADAMARD]
        
        g.add_edges(edges, edge_data=edge_types)

        # 3. Verification
        with g._get_session() as session:
            # Check edge 1->2 specifically
            res = session.run(
                """
                MATCH (n {graph_id: $gid, id: 1})-[r:Wire]->(m {graph_id: $gid, id: 2}) 
                RETURN r.t as t
                """, 
                gid=g.graph_id
            ).single()
            
        assert res is not None
        assert res['t'] == EdgeType.HADAMARD.value

    def test_add_edges_duplicates(self, neo4j_graph_e2e: GraphNeo4j):
        """
        Testataan että kaikki toimii duplikaattien osalta
        """
        g = neo4j_graph_e2e
        g.create_graph([{"id": 0}, {"id": 1}], [])

        # Lisää sama kahdesti
        g.add_edges([(0, 1)])
        g.add_edges([(0, 1)])

        with g._get_session() as session:
            count = session.run(
                """
                MATCH (n {graph_id: $gid, id: 0})-[r:Wire]->(m {graph_id: $gid, id: 1}) 
                RETURN count(r) as c
                """, 
                gid=g.graph_id
            ).single()['c']
