# Working zxdb.py

# CURRENTLY WORKING ZXDB HÄSSÄKKÄ

from fractions import Fraction
from neo4j import GraphDatabase
import json
import os
from typing import Optional
import logging
import time
from typing import (
    Any,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

import numpy as np
import pyzx as zx
from pyzx.utils import VertexType

from .pyzx_utils import pi_string_to_fraction
import networkx as nx

# Configure logging
logging.basicConfig(
    filename='app.log',            # Log file name
    filemode='w',                  # Append mode ('w' for overwrite)
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO             # Minimum logging level
)

class ZXdb:
    
    def __init__(self, uri = "bolt://localhost:7687", user = "", password="", graph_id: Optional['str'] = None):
        self.uri = uri
        self.user = user
        self.password = password
        self.basic_rewrite_rule_queries = {}
        self.main_rewrite_rule_queries = {}
        self._driver = None
        self.graph_id = graph_id if graph_id is not None else "graph_test_zxdb"
        self.current_path = os.path.dirname(os.path.abspath(__file__))

        with open(f"{self.current_path}/query_collections/memgraph-collection-zxdb.json", "r") as f:
            query_collection = json.load(f)

        for e in query_collection["items"]:
            self.basic_rewrite_rule_queries[e["title"]] = e

        with open(f"{self.current_path}/query_collections/collection-Rewrite-queries-ZXdb.json", "r") as f:
            query_collection = json.load(f)

        for e in query_collection["items"]:
            self.basic_rewrite_rule_queries[e["title"]] = e
        
        with open(f"{self.current_path}/query_collections/collection-Labeling-queries-ZXdb.json", "r") as f:
            query_collection = json.load(f)

        for e in query_collection["items"]:
            self.basic_rewrite_rule_queries[e["title"]] = e

        with open(f"{self.current_path}/query_collections/main_queries.json", "r") as f:
            query_collection = json.load(f)

        for e in query_collection["items"]:
            title = e["title"]
            self.basic_rewrite_rule_queries[title] = e
            self.main_rewrite_rule_queries[title] = e

        # Execute the following query first: STORAGE MODE IN_MEMORY_ANALYTICAL or STORAGE MODE IN_MEMORY_TRANSACTIONAL;
        # with self.driver.session() as analyze_session:
        #     analyze_session.run("STORAGE MODE IN_MEMORY_ANALYTICAL;")

    @property
    def driver(self):
        """Create driver only when needed"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self._driver
    
    
    def close(self):
        """Explicitly close the driver"""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
    

    def __enter__(self):
        return self
    

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def clear_all_data(self) -> None:
        """Clear all data from db"""
        with self.driver.session() as session:

            def clear_graph(tx):
                tx.run("""
                    MATCH (n) DETACH DELETE n
                """, graph_id=self.graph_id)
                
                return True

            session.execute_write(clear_graph)


    def empty_graphdb(self) -> None:
        """
        Clear all data from the graph database for a specific graph_id.
        
        Args:
            graph_id: Identifier for the graph to clear
        """
    
        with self.driver.session() as session:

            def clear_graph(tx):
                tx.run("""
                    MATCH (v:Node {graph_id: $graph_id})
                    DETACH DELETE v
                """, graph_id=self.graph_id)
                
                return True

            session.execute_write(clear_graph)
            logging.info(f"Cleared graph with ID '{self.graph_id}'")


    def export_graphdb_to_zx_graph(self,
        json_file_path: str
        ) -> zx.Graph:
        """
        Export a graph from Neo4j or Memgraph database to a PyZX graph and write JSON.
        Positions are computed (spring layout) and stored so they appear as 'pos' in JSON.
        """
        g = zx.Graph()

        with self.driver.session() as session:

            def fetch_graph_data(tx):
                vertices_query = """
                    MATCH (v:Node {graph_id: $graph_id})
                    RETURN id(v) AS id, v.t AS t, v.phase AS phase
                """
                edges_query = """
                    MATCH (source:Node {graph_id: $graph_id})-[r:Wire]->(target:Node {graph_id: $graph_id})
                    RETURN id(source) AS source_id, id(target) AS target_id, r.t AS t
                """
                input_vertices_query = """
                    MATCH (v:Node:Input {graph_id: $graph_id})
                    RETURN id(v) AS id
                """
                output_vertices_query = """
                    MATCH (v:Node:Output {graph_id: $graph_id})
                    RETURN id(v) AS id
                """

                vertices = tx.run(vertices_query, graph_id=self.graph_id).data()
                edges = tx.run(edges_query, graph_id=self.graph_id).data()
                inputs = tx.run(input_vertices_query, graph_id=self.graph_id).data()
                outputs = tx.run(output_vertices_query, graph_id=self.graph_id).data()
                return vertices, edges, inputs, outputs

            vertices, edges, inputs, outputs = session.execute_read(fetch_graph_data)

            # Add vertices
            vertex_ids = {}
            for vertex in vertices:
                t = vertex['t']
                if t == 0:
                    vtype = VertexType.BOUNDARY
                elif t == 1:
                    vtype = VertexType.Z
                elif t == 2:
                    vtype = VertexType.X
                elif t == 3:
                    vtype = VertexType.H_BOX
                elif t == 4:
                    vtype = VertexType.W_INPUT
                elif t == 5:
                    vtype = VertexType.W_OUTPUT
                elif t == 6:
                    vtype = VertexType.Z_BOX
                else:
                    raise ValueError(f"Unknown vertex type: {t}")

                phase_raw = vertex.get('phase', None)
                phase_frac = None
                if phase_raw is not None:
                    if isinstance(phase_raw, (int, float)):
                        phase_frac = Fraction(phase_raw).limit_denominator()  # interpreted as multiple of π
                    elif isinstance(phase_raw, str):
                        try:
                            # If it's a π-string like "3π/2" use your parser, else treat as decimal multiple of π
                            phase_frac = pi_string_to_fraction(phase_raw)
                        except Exception:
                            phase_frac = Fraction(phase_raw).limit_denominator()
                vid = g.add_vertex(ty=vtype, phase=phase_frac)
                vertex_ids[vertex['id']] = vid

            # Add undirected edges, map type, avoid duplicates
            seen = set()
            for edge in edges:
                u = vertex_ids[edge['source_id']]
                v = vertex_ids[edge['target_id']]
                if u == v:
                    continue
                key = (min(u, v), max(u, v))
                if key in seen:
                    continue
                seen.add(key)
                etype = zx.EdgeType.HADAMARD if edge.get('t', 1) == 2 else zx.EdgeType.SIMPLE
                g.add_edge(key, edgetype=etype)

            # IO sets
            # Filter and sort inputs/outputs as in correct usage
            input_vertices = [v for v in g.vertices() if v in [vertex_ids[input_v['id']] for input_v in inputs]]
            output_vertices = [v for v in g.vertices() if v in [vertex_ids[output_v['id']] for output_v in outputs]]
            input_vertices = sorted(input_vertices, key=g.qubit)
            output_vertices = sorted(output_vertices, key=g.qubit)
            g.set_inputs(tuple(input_vertices))
            g.set_outputs(tuple(output_vertices))

            # Compute positions (spring layout) so JSON contains "pos"
            nxg = nx.Graph()
            for v in g.vertices():
                nxg.add_node(v)
            for u, v in g.edges():
                nxg.add_edge(u, v)
            pos = nx.spring_layout(
                nxg,
                seed=42,
                k=100,  # larger k -> more spacing
                )
            for v, (x, y) in pos.items():
                g.set_position(v, float(x), float(y))

            #g.normalize()

            # Write JSON (to_json returns a JSON string)
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json.loads(g.to_json()), f, indent = 4)

            logging.info(f"Graph data exported to {json_file_path}")

        return g


    def import_zx_graph_json_to_graphdb(self,
        json_file_path: str,
        save_metadata: bool = True,
        initialize_empty: bool = False,
        batch_size: int = 5000,
        hadamard_edges: bool = False
        ) -> None:
        """
        Import a graph JSON file into Neo4j or Memgraph database, storing only vertices and edges.
        Uses efficient batch operations for faster imports.
        
        Args:
            json_file_path: Path to the JSON file containing graph data
            uri: URI for the Neo4j/Memgraph instance
            user: Database username
            password: Database password
            graph_id: Optional identifier for the graph (uses filename if not provided)
            save_metadata: Whether to save metadata to a separate file
            initialize_empty: Whether to clear existing graph data before import
            batch_size: Number of elements to include in each batch operation
        
        The function creates:
        - Vertex nodes with properties
        - Relationships between vertices based on edges
        """
        # Load JSON data
        with open(json_file_path, 'r') as f:
            graph_data = json.load(f)
        
        # Extract graph ID from file path if not provided
        
        # Save metadata to separate file if requested
        if save_metadata:
            metadata = {
                "graph_id": self.graph_id,
                "version": graph_data.get("version"),
                "backend": graph_data.get("backend"),
                "variable_types": graph_data.get("variable_types", {}),
                "scalar": graph_data.get("scalar", {}),
                "vertices": len(graph_data.get("vertices", [])),
                "edges": len(graph_data.get("edges", [])),
                "inputs": len(graph_data.get("inputs", [])),
                "outputs": len(graph_data.get("outputs", []))
            }
            
            metadata_file = f"{os.path.splitext(json_file_path)[0]}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logging.info(f"Metadata saved to {metadata_file}")
            
        with self.driver.session() as session:
            session.run("CREATE INDEX ON :Node(id);")
            session.run("CREATE INDEX ON :Node(t);")
            session.run("CREATE EDGE INDEX ON :Wire(id);")
            session.run("CREATE EDGE INDEX ON :Wire(t);")
        
        # Clear existing graph data if requested
        if initialize_empty:
            with self.driver.session() as session:
                def clear_existing_graph(tx):
                    tx.run("""
                        MATCH (v)
                        DETACH DELETE v
                    """, graph_id=self.graph_id)
                    
                    return True
                
                session.execute_write(clear_existing_graph)
                
                logging.info(f"Cleared existing graph with ID '{self.graph_id}'")
        
        with self.driver.session() as session:
            def create_vertices(tx):
                # Prepare and process vertices in batches
                vertices = graph_data.get("vertices", [])
                for i in range(0, len(vertices), batch_size):
                    batch = vertices[i:i+batch_size]
                    vertices_batch = []
                    
                    for vertex in batch:
                        # Create vertex properties dictionary
                        vertex_props = {
                            "graph_id": self.graph_id,
                            "id": vertex["id"],
                            "t": vertex.get("t")
                        }

                        if "phase" in vertex:
                            vertex_props["phase"] = float(pi_string_to_fraction(vertex["phase"]))
                        else:
                            if vertex.get("t") != 0:
                                # Default to 0 if phase is not a valid number or string
                                vertex_props["phase"] = 0
                        
                        # Add any additional properties
                        for k, v in vertex.items():
                            if k not in ["id", "t", "pos", "phase"]:
                                vertex_props[k] = v
                        
                        vertices_batch.append(vertex_props)
                    
                    # Batch create vertices
                    if vertices_batch:
                        tx.run("""
                            UNWIND $vertices AS vertex
                            CREATE (v:Node)
                            SET v = vertex
                        """, vertices=vertices_batch)
                        
                    logging.info(f"Vertex batch {i} of {np.ceil(len(vertices) / batch_size)} stored.")
                
                # Batch mark input vertices with Input label in batches
                if "inputs" in graph_data and graph_data["inputs"]:
                    inputs = graph_data["inputs"]
                    for i in range(0, len(inputs), batch_size):
                        batch = inputs[i:i+batch_size]
                        tx.run("""
                            UNWIND $input_ids AS input_id
                            MATCH (v:Node {graph_id: $graph_id, id: input_id})
                            SET v:Input
                        """, graph_id=self.graph_id, input_ids=batch)
                
                # Batch mark output vertices with Output label in batches
                if "outputs" in graph_data and graph_data["outputs"]:
                    outputs = graph_data["outputs"]
                    for i in range(0, len(outputs), batch_size):
                        batch = outputs[i:i+batch_size]
                        tx.run("""
                            UNWIND $output_ids AS output_id
                            MATCH (v:Node {graph_id: $graph_id, id: output_id})
                            SET v:Output
                        """, graph_id=self.graph_id, output_ids=batch)
                        
            session.execute_write(create_vertices)
            
                    
        with self.driver.session() as session:
            def create_edges(tx):
                # Prepare and process edges in batches
                edges = graph_data.get("edges", [])
                for i in range(0, len(edges), batch_size):
                    batch = edges[i:i+batch_size]
                    edges_batch = []
                    
                    for edge in batch:
                        # Edge format is [source_id, target_id, type]
                        if len(edge) >= 3:
                            edges_batch.append({
                                "source_id": edge[0],
                                "target_id": edge[1],
                                "t": edge[2],
                                "graph_id": self.graph_id
                            })
                    
                    # Batch create edges
                    if edges_batch:
                        tx.run("""
                            UNWIND $edges AS edge
                            MATCH (source:Node {graph_id: $graph_id, id: edge.source_id})
                            MATCH (target:Node {graph_id: $graph_id, id: edge.target_id})
                            CREATE (source)-[r:Wire {
                                t: edge.t,
                                graph_id: edge.graph_id
                            }]->(target)
                        """, edges=edges_batch, graph_id=self.graph_id)

                    logging.info(f"Edge batch {i} of {np.ceil(len(edges) / batch_size)} stored.")
                    
            session.execute_write(create_edges)
        
        if hadamard_edges:
            self.turn_hadamard_gates_into_edges(graph_id=self.graph_id)
            logging.info(f"Hadamard edges turned into gates for graph ID '{self.graph_id}'")


    @staticmethod
    def _coerce_rewrite_count(raw: Any) -> int:
        if raw is None:
            return 0
        if isinstance(raw, bool):
            return int(raw)
        if isinstance(raw, (int, float)):
            return int(raw)
        if isinstance(raw, str):
            try:
                return int(raw)
            except ValueError:
                return 0
        return 0


    @staticmethod
    def _summary_write_count(summary: Any) -> int:
        if summary is None or getattr(summary, "counters", None) is None:
            return 0
        counters = summary.counters
        return (
            int(getattr(counters, "nodes_created", 0))
            + int(getattr(counters, "nodes_deleted", 0))
            + int(getattr(counters, "relationships_created", 0))
            + int(getattr(counters, "relationships_deleted", 0))
            + int(getattr(counters, "properties_set", 0))
            + int(getattr(counters, "labels_added", 0))
            + int(getattr(counters, "labels_removed", 0))
        )


    def _execute_rewrite_query(self, tx, query: str, graph_id: Optional[str] = None) -> int:
        active_graph_id = self.graph_id if graph_id is None else graph_id
        result = tx.run(query, graph_id=active_graph_id)
        count = 0
        for record in result:
            values = record.values() if hasattr(record, "values") else []
            if values:
                count += self._coerce_rewrite_count(values[0])

        summary = result.consume()
        if count == 0 and self._summary_write_count(summary) > 0:
            return 1
        return count


    def _graph_signature(self) -> Tuple[int, int]:
        """Return a lightweight (node_count, edge_count) signature for this graph."""

        query = """
        MATCH (n:Node {graph_id: $graph_id})
        OPTIONAL MATCH (n)-[r:Wire]-()
        WITH count(DISTINCT n) AS nodes, count(DISTINCT r) AS edges
        RETURN nodes AS nodes, edges AS edges
        """

        with self.driver.session() as session:
            def read_signature(tx):
                rec = tx.run(query, graph_id=self.graph_id).single()
                if rec is None:
                    return (0, 0)
                return (int(rec["nodes"] or 0), int(rec["edges"] or 0))

            return session.execute_read(read_signature)


    def _boundary_degree_violations_tx(self, tx, graph_id: Optional[str] = None) -> int:
        """Count boundary vertices whose degree is not exactly 1."""

        active_graph_id = self.graph_id if graph_id is None else graph_id
        rec = tx.run(
            """
            MATCH (b:Node {graph_id: $graph_id, t: 0})
            OPTIONAL MATCH (b)-[r:Wire]-()
            WITH b, count(r) AS deg
            RETURN sum(CASE WHEN deg = 1 THEN 0 ELSE 1 END) AS bad
            """,
            graph_id=active_graph_id,
        ).single()
        return int(rec["bad"] or 0) if rec is not None else 0


    def _reindex_node_ids(self) -> int:
        """Assign contiguous integer ids to all nodes in this graph namespace."""

        query = """
        MATCH (n:Node {graph_id: $graph_id})
        WITH n ORDER BY id(n)
        WITH collect(n) AS nodes
        UNWIND CASE WHEN size(nodes) = 0 THEN [] ELSE range(0, size(nodes)-1) END AS idx
        WITH nodes[idx] AS n, idx
        SET n.id = idx
        RETURN count(n) AS reassigned
        """

        with self.driver.session() as session:
            def apply_reindex(tx):
                rec = tx.run(query, graph_id=self.graph_id).single()
                return int(rec["reassigned"] or 0) if rec is not None else 0

            return session.execute_write(apply_reindex)


    def hadamard_cancel_fn(self, session) -> int:
        total_patterns = 0
        while True:
            def mark_pattern(tx):
                # Get the marking query from your JSON collection
                mark_query = str(self.basic_rewrite_rule_queries["Hadamard cancellation labeling query"]["query"]["code"]["value"])
                result = tx.run(mark_query)
                record = result.single()
                return record["pattern_id"] if record and record["pattern_id"] else None
            
            pattern_id = session.execute_write(mark_pattern)
            if not pattern_id:
                break  # No more patterns found
            total_patterns += 1
        
        # Step 2: Process all marked patterns
        if total_patterns > 0:
            def cancel_patterns(tx):
                cancel_query = str(self.basic_rewrite_rule_queries["Hadamard edge cancellation"]["query"]["code"]["value"])
                result = tx.run(cancel_query, graph_id=self.graph_id)
                return result.single()["patterns_processed"]
            processed = session.execute_write(cancel_patterns)
        return total_patterns


    def hadamard_cancel(self) -> int:
        """
        Cancel Hadamard gates using iterative pattern labeling approach.
        """
        
        with self.driver.session() as session:
            total_patterns = 0
            start_time = time.time()
            # Step 1: Iteratively label patterns
            while True:
                def mark_pattern(tx):
                    # Get the marking query from your JSON collection
                    mark_query = str(self.basic_rewrite_rule_queries["Hadamard cancellation labeling query"]["query"]["code"]["value"])
                    result = tx.run(mark_query)
                    record = result.single()
                    return record["pattern_id"] if record and record["pattern_id"] else None
                
                pattern_id = session.execute_write(mark_pattern)
                if not pattern_id:
                    break  # No more patterns found
                total_patterns += 1
                logging.info(f"Marked pattern {pattern_id} for Hadamard cancellation in graph ID '{self.graph_id}'")
            
            # Step 2: Process all marked patterns
            if total_patterns > 0:
                def cancel_patterns(tx):
                    cancel_query = str(self.basic_rewrite_rule_queries["Hadamard edge cancellation"]["query"]["code"]["value"])
                    result = tx.run(cancel_query, graph_id=self.graph_id)
                    return result.single()["patterns_processed"]
                
                processed = session.execute_write(cancel_patterns)
                end_time = time.time()
                logging.info(f"Hadamard cancellation completed in {end_time - start_time} seconds for graph ID '{self.graph_id}'")
                logging.info(f"Hadamard cancellation: {total_patterns} patterns found, {processed} processed")
            
            return total_patterns


    def remove_identities(self) -> int:
        """
        Remove identity gates from the graph.
        
        Args:
            graph_id: Identifier for the graph to process
        """
        query_remove_identities = str(self.basic_rewrite_rule_queries["Remove identities with refactor"]["query"]["code"]["value"])

        total_removed = 0
        with self.driver.session() as session:
            while True:
                def process_identity_removal(tx):
                    return self._execute_rewrite_query(tx, query_remove_identities, self.graph_id)

                removed = session.execute_write(process_identity_removal)
                if removed == 0:
                    break
                total_removed += removed

        return total_removed
    

    def spider_fusion(self) -> int:
        """
        Perform spider fusion on the graph, matching spider_simp() behavior from simplify.py.
        Spider fusion fuses same-colored spiders connected by simple edges,
        then removes self-loops.
        
        Args:
            graph_id: Identifier for the graph to process
        
        Returns:
            Number of spider fusion patterns processed
        """
        # Use the bounded canonical rewrite (one merge per invocation), scoped to graph_id.
        # The JSON Spider fusion query can become very expensive on larger DB states.
        query = """
        MATCH (u:Node)-[e:Wire]-(v:Node)
        WHERE u.graph_id = $graph_id AND v.graph_id = $graph_id
          AND id(u) < id(v)
          AND u.t IN [1, 2] AND v.t IN [1, 2]
          AND ((e.t = 1 AND u.t = v.t) OR (e.t = 2 AND u.t <> v.t))

        WITH u, v
        ORDER BY u.id, v.id
        LIMIT 1

        OPTIONAL MATCH (v)-[ev:Wire]-(nv:Node)
        WHERE nv <> u
        WITH u, v, collect({node: nv, edge_t: ev.t}) AS v_neighbors

        SET u.phase = coalesce(toFloat(u.phase), 0.0) + coalesce(toFloat(v.phase), 0.0)
        DETACH DELETE v

        WITH u, v_neighbors
        UNWIND (CASE WHEN size(v_neighbors) = 0 THEN [null] ELSE v_neighbors END) AS vn
        WITH u, vn.node AS nv, vn.edge_t AS ev_t
        WHERE nv IS NOT NULL

        OPTIONAL MATCH (u)-[eu:Wire]-(nv)
        WITH u, nv, ev_t, eu, CASE WHEN eu IS NOT NULL THEN eu.t ELSE NULL END AS eu_t

        FOREACH (_ IN CASE WHEN eu IS NULL THEN [1] ELSE [] END |
            CREATE (u)-[:Wire {t: ev_t, graph_id: $graph_id}]->(nv)
        )
        FOREACH (_ IN CASE WHEN eu_t = 2 AND ev_t = 2 THEN [1] ELSE [] END |
            DELETE eu
        )
        FOREACH (_ IN CASE WHEN (eu_t = 1 AND ev_t = 2) OR (eu_t = 2 AND ev_t = 1) THEN [1] ELSE [] END |
            SET eu.t = 1
            SET nv.phase = coalesce(toFloat(nv.phase), 0.0) + 1.0
        )

        RETURN 1 AS rewrites_applied
        """

        with self.driver.session() as session:
            total_patterns = 0
            while True:
                def spider_fusion_batch(tx):
                    return self._execute_rewrite_query(tx, query, self.graph_id)

                merged = session.execute_write(spider_fusion_batch)
                total_patterns += merged

                if merged == 0:
                    break

            return total_patterns


    def remove_self_loop_simp(self) -> int:
        """Remove self-loops on ZX-like nodes; Hadamard self-loops add a pi phase."""

        self_loop_query = """
        MATCH (v:Node)-[r:Wire]-(v)
        WHERE v.graph_id = $graph_id AND v.t IN [1, 2]
        WITH v, COLLECT(r) AS loops,
             sum(CASE r.t WHEN 2 THEN 1 ELSE 0 END) AS had_count
        SET v.phase = coalesce(v.phase, 0) + CASE WHEN had_count % 2 = 1 THEN 1 ELSE 0 END
        FOREACH (loop IN loops | DELETE loop)
        RETURN count(DISTINCT v) AS rewrites_applied
        """

        with self.driver.session() as session:
            def apply_remove_self_loops(tx):
                return self._execute_rewrite_query(tx, self_loop_query, self.graph_id)

            return session.execute_write(apply_remove_self_loops)
        

    def pivot_rule(self, graph_id: Optional[str] = None) -> int:
        """
        Apply the pivot rule to the graph.

        Args:
            graph_id: Optional identifier for the graph to process.
                Uses self.graph_id when omitted.

        Returns:
            Number of pivot rule patterns processed
        """

        with self.driver.session() as session:
            active_graph_id = graph_id if graph_id is not None else self.graph_id

            query_two = str(self.main_rewrite_rule_queries["Pivot rule - two interior Pauli spiders"]["query"]["code"]["value"])
            # Guard against non-canonical matches that can disconnect boundaries.
            # We only allow pivoting true interior spiders whose non-pivot neighbors
            # are ZX spiders connected by Hadamard edges and are not degree-1 leaves.
            query_two = query_two.replace(
                '  AND b.phase = round(b.phase)',
                '  AND b.phase = round(b.phase)\n'
                '  AND size([(a)-[ea:Wire]-(na) WHERE na <> b AND ((ea.t <> 2) OR (coalesce(na.t, -1) <> 1) OR degree(na) = 1) | 1]) = 0\n'
                '  AND size([(b)-[eb:Wire]-(nb) WHERE nb <> a AND ((eb.t <> 2) OR (coalesce(nb.t, -1) <> 1) OR degree(nb) = 1) | 1]) = 0'
            )
            if "WITH a, b, pivot_edge" in query_two and "ORDER BY a.id" not in query_two:
                query_two = query_two.replace(
                    "WITH a, b, pivot_edge",
                    "WITH a, b, pivot_edge\nORDER BY a.id\nLIMIT 1",
                    1,
                )
            enable_single_interior_pauli = True
            query_single = (
                str(self.main_rewrite_rule_queries["Pivot rule - single interior Pauli spider"]["query"]["code"]["value"])
                if enable_single_interior_pauli
                else None
            )

            total_processed = 0
            while True:
                def apply_two(tx):
                    return self._execute_rewrite_query(tx, query_two, active_graph_id)

                c1 = session.execute_write(apply_two)

                if query_single is not None:
                    def apply_single(tx):
                        return self._execute_rewrite_query(tx, query_single, active_graph_id)

                    c2 = session.execute_write(apply_single)
                else:
                    c2 = 0

                if (c1 + c2) == 0:
                    break
                total_processed += (c1 + c2)

            return total_processed
        
        
    def local_complementation_rule(self) -> int:
        """
        Apply the local complementation rule to the graph.

        Args:
            graph_id: Identifier for the graph to process

        Returns:
            Number of local complementation patterns processed
        """

        with self.driver.session() as session:
            # Use the canonical guarded local-complement rule from memgraph_queries.
            # The JSON variant can match non-interior centers and disconnect boundaries.
            query = """
            MATCH (center:Node)
            WHERE center.graph_id = $graph_id
              AND center.t = 1
              AND (center.phase = 0.5 OR center.phase = -0.5 OR center.phase = 1.5)

            // PROTECT GADGETS
            OPTIONAL MATCH (center)-[bad_edge]-(bad_neighbor)
            WHERE NOT (bad_neighbor.t = 1 AND bad_edge.t = 2) OR degree(bad_neighbor) = 1
            WITH center, count(bad_neighbor) AS bad_connections
            WHERE bad_connections = 0

            MATCH (center)-[w:Wire {t:2}]-(nbr:Node {t:1})
            WITH center, collect(distinct nbr) AS neighbors
            WHERE size(neighbors) > 0 AND degree(center) = size(neighbors)

            WITH center, neighbors
            ORDER BY center.id
            LIMIT 1

            FOREACH (n IN neighbors |
                SET n.phase = coalesce(toFloat(n.phase), 0.0) - coalesce(toFloat(center.phase), 0.0)
            )

            WITH center, neighbors
            DETACH DELETE center

            WITH neighbors
            WHERE size(neighbors) >= 2
            UNWIND range(0, size(neighbors)-2) AS i
            UNWIND range(i+1, size(neighbors)-1) AS j
            WITH neighbors[i] AS n1, neighbors[j] AS n2

            OPTIONAL MATCH (n1)-[e:Wire]-(n2)
            WITH n1, n2, e, CASE WHEN e IS NOT NULL THEN e.t ELSE NULL END AS et

            FOREACH (_ IN CASE WHEN et IS NULL THEN [1] ELSE [] END |
                CREATE (n1)-[:Wire {t: 2, graph_id: $graph_id}]->(n2)
            )
            FOREACH (_ IN CASE WHEN et = 2 THEN [1] ELSE [] END |
                DELETE e
            )
            FOREACH (_ IN CASE WHEN et = 1 THEN [1] ELSE [] END |
                SET n1.phase = coalesce(toFloat(n1.phase), 0.0) + 1.0
            )

            RETURN 1 AS count
            """
            total_changed = 0

            while True:
                def apply_local_complementation(tx):
                    return self._execute_rewrite_query(tx, query, self.graph_id)

                changed = session.execute_write(apply_local_complementation)
                if changed == 0:
                    break  # No more patterns found

                total_changed += changed


            #end_time = time.time()
            #logging.info(f"Local complementation applied for graph ID '{graph_id}' with {changed} patterns processed in {end_time - start_time} seconds")
            return total_changed
        
    
    def phase_gadget_fusion_rule(self) -> int:
        """
        Apply the phase gadget fusion rule to the graph.

        Args:
            graph_id: Identifier for the graph to process

        Returns:
            Number of phase gadget fusion patterns processed
        """

        with self.driver.session() as session:
            total_changed = 0

            for title in ["Gadget fusion red green", "Gadget fusion Hadamard", "Gadget fusion both"]:
                if title not in self.basic_rewrite_rule_queries:
                    continue
                query = str(self.basic_rewrite_rule_queries[title]["query"]["code"]["value"])

                def apply_phase_gadget_fusion_rewrite(tx):
                    return self._execute_rewrite_query(tx, query, self.graph_id)

                total_changed += session.execute_write(apply_phase_gadget_fusion_rewrite)

            return total_changed
        

    def pivot_gadget_rule(self) -> int:
        """
        Apply the pivot gadget rule to the graph.

        Args:
            graph_id: Identifier for the graph to process

        Returns:
            Number of patterns processed
        """
        pgf_query = str(self.main_rewrite_rule_queries["Pivot gadget"]["query"]["code"]["value"])

        with self.driver.session() as session:
            def apply_pivot_gadget_labeling(tx):
                before_bad = self._boundary_degree_violations_tx(tx, self.graph_id)
                changed = self._execute_rewrite_query(tx, pgf_query, self.graph_id)
                if changed == 0:
                    return 0

                after_bad = self._boundary_degree_violations_tx(tx, self.graph_id)
                if after_bad > before_bad:
                    # Abort this transaction: pivot-gadget rewrite is not boundary-safe here.
                    raise RuntimeError("pivot_gadget_boundary_violation")

                return changed

            try:
                return session.execute_write(apply_pivot_gadget_labeling)
            except RuntimeError as exc:
                if str(exc) == "pivot_gadget_boundary_violation":
                    logging.info(
                        "Skipping pivot gadget rewrite that violates boundary degree for graph ID '%s'",
                        self.graph_id,
                    )
                    return 0
                raise
        

    def pivot_boundary_rule(self) -> int:
        """
        Apply the pivot boundary rule to the graph.

        Args:
            graph_id: Identifier for the graph to process

        Returns:
            Number of patterns processed
        """
        pb_query = str(self.main_rewrite_rule_queries["Pivot boundary"]["query"]["code"]["value"])

        with self.driver.session() as session:
            def apply_pivot_boundary_labeling(tx):
                return self._execute_rewrite_query(tx, pb_query, self.graph_id)

            return session.execute_write(apply_pivot_boundary_labeling)


    def bialgebra_simp(self) -> int:
        """
        Apply the bialgebra rule to the graph.

        Args:
            graph_id: Identifier for the graph to process

        Returns:
            Number of patterns processed
        """

        with self.driver.session() as session:
            total_changed = 0
            for title in ["Bialgebra red-green", "Bialgebra Hadamard", "Bialgebra simplification"]:
                if title not in self.basic_rewrite_rule_queries:
                    continue
                query = str(self.basic_rewrite_rule_queries[title]["query"]["code"]["value"])

                def apply_bialgebra(tx):
                    return self._execute_rewrite_query(tx, query, self.graph_id)

                total_changed += session.execute_write(apply_bialgebra)

            return total_changed
        

    def get_degree_distribution(self) -> dict:
        """
        Get the degree distribution of the graph.

        Args:
            graph_id: Identifier for the graph to process

        Returns:
            Dictionary mapping degree to count of vertices with that degree
        """

        degree_distribution = {}

        with self.driver.session() as session:
            def fetch_degree_distribution(tx):
                query = str(self.basic_rewrite_rule_queries["Get degree distribution"]["query"]["code"]["value"])
                result = tx.run(query, graph_id=self.graph_id)
                return {record["degree"]: record["frequency"] for record in result}

            degree_distribution = session.execute_read(fetch_degree_distribution)

        return degree_distribution
    

    def turn_hadamard_gates_into_edges(self) -> None:
        """
        Turn Hadamard gates into edges in the graph.

        Args:
            graph_id: Identifier for the graph to process
        """

        with self.driver.session() as session:
            def apply_hadamard_to_edge_conversion(tx):
                query = str(self.basic_rewrite_rule_queries["Turn Hadamard gates into Hadamard edges"]["query"]["code"]["value"])
                tx.run(query, graph_id=self.graph_id)

            session.execute_write(apply_hadamard_to_edge_conversion)

    def copy_simp(self) -> int:
        """
        Perform the copy simp operation
        """
        with self.driver.session() as session:
            def apply_copy_simp(tx):
                query = str(self.basic_rewrite_rule_queries["State copy"]["query"]["code"]["value"])
                return self._execute_rewrite_query(tx, query, self.graph_id)

            return session.execute_write(apply_copy_simp)

    def to_gh(self) -> None:
        """
        Change color of all red vertices to green
        """
        with self.driver.session() as session:
            def apply_change_color(tx):
                query = str(self.basic_rewrite_rule_queries["Change color"]["query"]["code"]["value"])
                tx.run(query, graph_id=self.graph_id)

            session.execute_write(apply_change_color)
    
    def remove_isolated_vertices(self) -> None:
            """
            Remove isolated vertices from the graph.
            Also remove dangling pairs of vertices that aren't connected to the graph but only to each other.
            """
            with self.driver.session() as session:
                def _remove_operations(tx):
                    tx.run("""
                        MATCH (n:Node {graph_id: $graph_id})-[r:Wire]-(m:Node {graph_id: $graph_id})
                                                WHERE id(n) < id(m)
                                                    AND degree(n) = 1 AND degree(m) = 1
                                                    AND coalesce(n.t, -1) <> 0 AND coalesce(m.t, -1) <> 0
                        DETACH DELETE n, m
                        WITH count(*) AS deleted_pairs

                        MATCH (v:Node {graph_id: $graph_id})
                                                WHERE degree(v) = 0 AND coalesce(v.t, -1) <> 0
                        DELETE v
                        RETURN deleted_pairs + count(v) AS removed;
                        """, graph_id=self.graph_id)

                session.execute_write(_remove_operations)

    def supplementarity_simp(self) -> int:
        """
        Apply the supplementarity rule to the graph.
        Removes pairs of non-Clifford spiders that have the same set of neighbors.
        """
        count = 0
        with self.driver.session() as session:
            while True:
                def _supp_type_1(tx):
                    # Type 1: Disconnected, same neighbors
                    # Check conditions: 
                    # 1. Z-spiders (t:1)
                    # 2. Non-Clifford phases (approx check if phase * 2 is integer)
                    # 3. Disconnected
                    # 4. Same degree
                    # 5. Same neighbors (inclusion + same degree)
                    query = """
                    MATCH (v:Node {graph_id: $graph_id, t: 1}), (w:Node {graph_id: $graph_id, t: 1})
                    WHERE id(v) < id(w)
                      AND NOT (v)-[:Wire]-(w)
                      AND abs((v.phase * 2) - round(v.phase * 2)) > 1e-5
                      AND abs((w.phase * 2) - round(w.phase * 2)) > 1e-5
                      AND size((v)-[:Wire]-()) = size((w)-[:Wire]-())
                      AND size([(v)-[:Wire]-(n) WHERE NOT (n)-[:Wire]-(w) | 1]) = 0
                    WITH v, w
                    WITH v, w, v.phase + w.phase AS s, v.phase - w.phase AS d
                    WITH v, w,
                         (abs(s - round(s)) < 1e-5 AND toInteger(round(s)) % 2 <> 0) AS sum_odd,
                         (abs(d - round(d)) < 1e-5 AND toInteger(round(d)) % 2 <> 0) AS diff_odd
                    WHERE sum_odd OR diff_odd
                    OPTIONAL MATCH (v)-[:Wire]-(n)
                    FOREACH (_ IN CASE WHEN sum_odd THEN [1] ELSE [] END | 
                        SET n.phase = coalesce(n.phase, 0.0) + 1.0
                    )
                    DETACH DELETE v, w
                    RETURN count(*) as c
                    """
                    result = tx.run(query, graph_id=self.graph_id)
                    record = result.single()
                    return record["c"] if record else 0

                c1 = session.execute_write(_supp_type_1)
                
                def _supp_type_2(tx):
                    # Type 2: Connected, same neighbors (excluding each other)
                    # Check conditions:
                    # 1. Z-spiders (t:1)
                    # 2. Non-Clifford phases
                    # 3. Connected
                    # 4. Same degree
                    # 5. Same other neighbors
                    query = """
                    MATCH (v:Node {graph_id: $graph_id, t: 1}), (w:Node {graph_id: $graph_id, t: 1})
                    WHERE id(v) < id(w)
                      AND (v)-[:Wire]-(w)
                      AND abs((v.phase * 2) - round(v.phase * 2)) > 1e-5
                      AND abs((w.phase * 2) - round(w.phase * 2)) > 1e-5
                      AND size((v)-[:Wire]-()) = size((w)-[:Wire]-())
                      AND size([(v)-[:Wire]-(n) WHERE n <> w AND NOT (n)-[:Wire]-(w) | 1]) = 0
                    WITH v, w
                    WITH v, w, v.phase + w.phase AS s, v.phase - w.phase AS d
                    WITH v, w,
                         (abs(s - round(s)) < 1e-5 AND toInteger(round(s)) % 2 = 0) AS sum_even,
                         (abs(d - round(d)) < 1e-5 AND toInteger(round(d)) % 2 <> 0) AS diff_odd
                    WHERE sum_even OR diff_odd
                    OPTIONAL MATCH (v)-[:Wire]-(n)
                    WHERE n <> w
                    FOREACH (_ IN CASE WHEN sum_even THEN [1] ELSE [] END | 
                        SET n.phase = coalesce(n.phase, 0.0) + 1.0
                    )
                    DETACH DELETE v, w
                    RETURN count(*) as c
                    """
                    result = tx.run(query, graph_id=self.graph_id)
                    record = result.single()
                    return record["c"] if record else 0

                c2 = session.execute_write(_supp_type_2)
                
                if c1 == 0 and c2 == 0:
                    break
                count += c1 + c2
        
        return count

    def interior_clifford_simp(self):
        self.to_gh()
        applied_any = False
        while True:
            i1 = self.remove_identities()
            i2 = self.spider_fusion()
            i_self = self.remove_self_loop_simp()
            i3 = self.pivot_rule()
            i4 = self.local_complementation_rule()

            if not (i1 or i2 or i_self or i3 or i4):
                break
            applied_any = True

        return applied_any
    
    def clifford_simp(self):
        applied_any = False
        while True:
            i = self.interior_clifford_simp()
            i2 = self.pivot_boundary_rule()
            if i or i2:
                applied_any = True
            if not i2:
                break
        return applied_any

    def full_reduce(self, max_main_iterations: int = 200, pivot_only_stall_limit: int = 6):
        self.interior_clifford_simp()
        self.pivot_gadget_rule()

        pivot_only_stall = 0
        previous_signature = self._graph_signature()

        for _ in range(max_main_iterations):
            self.clifford_simp()
            i = self.phase_gadget_fusion_rule()
            self.interior_clifford_simp()
            k = self.copy_simp()
            l = self.supplementarity_simp()
            j = self.pivot_gadget_rule()

            current_signature = self._graph_signature()

            if not (i or k or l):
                if j == 0:
                    self.remove_isolated_vertices()
                    self._reindex_node_ids()
                    return

                # Pivot-gadget rewrites can oscillate in place on some inputs.
                # If only pivot-gadget fires and the graph signature stays fixed,
                # stop after a few rounds to ensure termination.
                if current_signature == previous_signature:
                    pivot_only_stall += 1
                else:
                    pivot_only_stall = 0

                if pivot_only_stall >= pivot_only_stall_limit:
                    logging.info(
                        "Stopping full_reduce after pivot-only stall for graph ID '%s'",
                        self.graph_id,
                    )
                    self.remove_isolated_vertices()
                    self._reindex_node_ids()
                    return
            else:
                pivot_only_stall = 0

            previous_signature = current_signature

            if not (i or k or j or l):
                self.remove_isolated_vertices()
                self._reindex_node_ids()
                return

        logging.warning(
            "full_reduce reached max_main_iterations=%s for graph ID '%s'",
            max_main_iterations,
            self.graph_id,
        )
        self.remove_isolated_vertices()
        self._reindex_node_ids()