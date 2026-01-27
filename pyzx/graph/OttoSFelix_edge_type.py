def edge_type(self, e: ET) -> EdgeType:
        """Returns the type of the given edge:
        ``EdgeType.SIMPLE`` if it is regular, ``EdgeType.HADAMARD`` if it is a Hadamard edge,
        0 if the edge is not in the graph."""

        query = """MATCH (n1:Node {graph_id: $graph_id, id: $node1}) -[r:Wire]-(n2:Node {graph_id: $graph_id, id: $node2}) RETURN r.t"""
        with self._get_session() as session:
                    result = session.execute_read(
                    lambda tx: tx.run(query, graph_id=self.graph_id, node1=e[0], node2=e[1]).data()
                )
        return EdgeType(result[0]['r.t']) if len(result) > 0 else 0