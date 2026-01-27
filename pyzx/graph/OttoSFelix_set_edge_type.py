def set_edge_type(self, e: ET, t: EdgeType) -> None:
        """Sets the type of the given edge."""
        query = """MATCH (n1:Node {graph_id: $graph_id, id: $node1}) -[r:Wire]-(n2:Node {graph_id: $graph_id, id: $node2}) SET r.t = $type"""
        with self._get_session() as session:
                    session.execute_write(
                    lambda tx: tx.run(query, graph_id=self.graph_id, node1=e[0], node2=e[1], type=t)
                )
