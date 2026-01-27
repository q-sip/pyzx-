def set_type(self, vertex: VT, t: VertexType) -> None:
        """Sets the type of the given vertex to t."""

        query = """MATCH (n:Node {graph_id: $graph_id, id: $id}) SET n.t = $type"""
        with self._get_session() as session:
            session.execute_write(
            lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex, type=t)
            )
