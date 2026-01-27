def type(self, vertex: VT) -> VertexType:
        """Returns the type of the given vertex:
        VertexType.BOUNDARY if it is a boundary, VertexType.Z if it is a Z node,
        VertexType.X if it is a X node, VertexType.H_BOX if it is an H-box."""

        query = """MATCH (n:Node {graph_id: $graph_id, id: $id}) RETURN n.t"""
        with self._get_session() as session:
                    result = session.execute_read(
                    lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex).data()
                )
        return VertexType(result[0]['n.t'])