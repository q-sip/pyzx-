def set_phase(self, vertex: VT, phase: FractionLike) -> None:
        """Sets the phase of the vertex to the given value."""
        query = """MATCH (n:Node {graph_id: $graph_id, id: $id}) SET n.phase = $phase"""
        with self._get_session() as session:
            session.execute_write(
            lambda tx: tx.run(query, graph_id=self.graph_id, id=vertex, phase=self._phase_to_str(phase))
            )