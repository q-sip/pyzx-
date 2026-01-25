# tests/test_graph_neo4j/test_remove_edges.py
from pyzx.utils import EdgeType, VertexType
from pyzx.graph.graph_neo4j import GraphNeo4j


class TestRemoveEdges:
    #Testaa relationshippien poistamista Neo4j-graphista

    def test_remove_single_edge(self, neo4j_graph_e2e: GraphNeo4j):
        # Testataan yhden relationshipin poistaminen
        g = neo4j_graph_e2e

        nodes = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 1, "qubit": 0},
            {"ty": VertexType.X, "row": 2, "qubit": 0},
        ]
        edges = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.SIMPLE),
        ]
        g.create_graph(nodes, edges)

        initial_edge_count = self._count_edges(g)
        assert initial_edge_count == 2

        g.remove_edges([(0, 1)])

        final_edge_count = self._count_edges(g)
        assert final_edge_count == 1

        assert not self._edge_exists(g, 0, 1)
        assert self._edge_exists(g, 1, 2)

    def test_remove_multiple_edges(self, neo4j_graph_e2e: GraphNeo4j):
        #Testataan useamman relationshipin poistaminen kerralla

        g = neo4j_graph_e2e

        nodes = [
            {"ty": VertexType.BOUNDARY},
            {"ty": VertexType.Z},
            {"ty": VertexType.X},
            {"ty": VertexType.BOUNDARY},
        ]
        edges = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 3), EdgeType.SIMPLE),
        ]
        g.create_graph(nodes, edges)


        assert self._count_edges(g) == 3


        g.remove_edges([(0, 1), (2, 3)])


        assert self._count_edges(g) == 1
        assert not self._edge_exists(g, 0, 1)
        assert self._edge_exists(g, 1, 2)
        assert not self._edge_exists(g, 2, 3)

    def test_remove_edges_empty_list(self, neo4j_graph_e2e: GraphNeo4j):
        #Testataan tyhjällä listalla poistaminen ja varmistetaan, että mikään ei muutu

        g = neo4j_graph_e2e


        nodes = [{"ty": VertexType.Z}, {"ty": VertexType.X}]
        edges = [((0, 1), EdgeType.SIMPLE)]
        g.create_graph(nodes, edges)

        initial_count = self._count_edges(g)


        g.remove_edges([])


        assert self._count_edges(g) == initial_count

    def test_remove_nonexistent_edge(self, neo4j_graph_e2e: GraphNeo4j):
        #Testataan, että olemattoman relationshipin poistaminen ei aiheuta virheitä

        g = neo4j_graph_e2e


        nodes = [
            {"ty": VertexType.Z},
            {"ty": VertexType.X},
            {"ty": VertexType.BOUNDARY},
        ]
        edges = [((1, 2), EdgeType.SIMPLE)]
        g.create_graph(nodes, edges)

        initial_count = self._count_edges(g)


        g.remove_edges([(0, 1)])


        assert self._count_edges(g) == initial_count
        assert self._edge_exists(g, 1, 2)

    def test_remove_edges_bidirectional(self, neo4j_graph_e2e: GraphNeo4j):
        #Varmistetaan, että relationshipit voidaan poistaa kumpaankin suuntaan
        g = neo4j_graph_e2e


        nodes = [{"ty": VertexType.Z}, {"ty": VertexType.X}]
        edges = [((0, 1), EdgeType.SIMPLE)]
        g.create_graph(nodes, edges)

        assert self._edge_exists(g, 0, 1)


        g.remove_edges([(1, 0)])


        assert not self._edge_exists(g, 0, 1)
        assert not self._edge_exists(g, 1, 0)

    def test_remove_hadamard_edge(self, neo4j_graph_e2e: GraphNeo4j):
        #Testataan Hadarmardin poistaminen
        g = neo4j_graph_e2e


        nodes = [{"ty": VertexType.Z}, {"ty": VertexType.Z}]
        edges = [((0, 1), EdgeType.HADAMARD)]
        g.create_graph(nodes, edges)

        assert self._count_edges(g) == 1

        g.remove_edges([(0, 1)])


        assert self._count_edges(g) == 0

    def _count_edges(self, g: GraphNeo4j) -> int:
        #Lasketaan relationshipit graafissa
        query = """
        MATCH (n:Node {graph_id: $gid})-[r:Wire]->(m:Node {graph_id: $gid})
        RETURN count(r) as count
        """
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id).single()
            return result["count"] if result else 0

    def _edge_exists(self, g: GraphNeo4j, src: int, tgt: int) -> bool:
        #Varmistetaan, että relationship on olemassa kahden noden välillä
        
        query = """
        MATCH (n:Node {graph_id: $gid, id: $src})-[r:Wire]-(m:Node {graph_id: $gid, id: $tgt})
        RETURN count(r) > 0 as exists
        """
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id, src=src, tgt=tgt).single()
            return result["exists"] if result else False
