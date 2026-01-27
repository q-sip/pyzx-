def incident_edges(self, vertex: VT) -> Sequence[ET]:
    """Returns all neighboring edges of the given vertex."""

    query = """
    MATCH (n:Node {graph_id: $graph_id, id: $vertex})-[r:Wire]-(m:Node {graph_id: $graph_id})
    RETURN m.id AS neighbor
    """

    with self._get_session() as session:
        result = session.execute_read(
        lambda tx: tx.run(query, graph_id=self.graph_id, vertex=vertex).data()
        )

    return [
        (vertex, r["neighbor"])
        for r in result
    ]
