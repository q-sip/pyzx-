from pyzx.graph.neo4j_rewrite_runner import run_rewrite, run_rewrites

# If you already have a Neo4j driver:
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "testkala"))

def session_factory():
    return driver.session(database="neo4j")  # or your db name

# Run a single rule
result, elapsed = run_rewrite(
    session_factory,
    graph_id="test_graph",
    rule_name="spider_fusion",
    variant_id="SPIDER_FUSION_2",
)

print(result, elapsed)

# Run all registered rules
results = run_rewrites(
    session_factory,
    graph_id="test_graph",
    rules=["spider_fusion"],
    query_config={"spider_fusion": "SPIDER_FUSION_2"},
    measure_time=True,
)
print(results)