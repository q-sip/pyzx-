def edges(self, s: Optional[VT]=None, t: Optional[VT]=None) -> Iterable[ET]:
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
                lambda tx: tx.run(query, graph_id=self.graph_id, vertices=vertices_payload).data()
            )
            return [(item['src'], item['tgt']) for item in result]
        else:
            query = "MATCH (n1:Node {graph_id: $graph_id})-[r:Wire]->(n2:Node {graph_id: $graph_id}) RETURN n1.id, n2.id"
            with self._get_session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, graph_id=self.graph_id).data()
                )
            return [(item['n1.id'], item['n2.id']) for item in result]