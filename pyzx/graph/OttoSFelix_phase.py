def phase(self, vertex: VT) -> FractionLike:
        """Returns the phase value of the given vertex."""
        query = """MATCH (n:Node {graph_id: $graph_id, id: $id}) RETURN n.phase"""
        with self._get_session() as session:
                    result = session.execute_read(
                    lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex).data()
                )
        if not result:
            return None
        p = result[0]['n.phase']
        if p is None:
            return None
        try:
            return Fraction(p)
        except ValueError:
            try:
                return parse(p, lambda x: new_var(x, False))
            except Exception:
                return Fraction(0)