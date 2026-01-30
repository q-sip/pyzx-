# tests/test_graph_neo4j/conftest.py
import os
import uuid
from dotenv import load_dotenv
import pytest
from pyzx.graph.graph_neo4j import GraphNeo4j


def _neo4j_env_present() -> bool:

    return all(os.getenv(k) for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"))


@pytest.fixture
def unique_graph_id() -> str:
    return f"test_graph_{uuid.uuid4().hex}"


@pytest.fixture(autouse=True)
def _patch_phase_to_str_if_missing(monkeypatch):
    if not hasattr(GraphNeo4j, "_phase_to_str"):
        monkeypatch.setattr(
            GraphNeo4j,
            "_phase_to_str",
            lambda self, phase: "0" if phase is None else str(phase),
            raising=False,
        )


@pytest.fixture
def neo4j_graph_unit(unique_graph_id):
    """
    Unit-test graph: DB calls should be mocked per-test.
    """
    g = GraphNeo4j(
        uri="bolt://unit-test-does-not-connect",
        user="neo4j",
        password="password",
        graph_id=unique_graph_id,
        database=os.getenv("NEO4J_DATABASE"),
    )
    yield g
    g.close()


@pytest.fixture
def neo4j_graph_e2e(unique_graph_id):
    """
    End-to-end graph: requires reachable Neo4j; skips if not available.
    """
    if not _neo4j_env_present():
        pytest.skip("Neo4j env vars missing (NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD).")

    g = GraphNeo4j(
        uri=os.getenv("NEO4J_URI", ""),
        user=os.getenv("NEO4J_USER", ""),
        password=os.getenv("NEO4J_PASSWORD", ""),
        graph_id=unique_graph_id,
        database=os.getenv("NEO4J_DATABASE"),
    )

    # sanity-check connection
    try:
        with g._get_session() as session:
            session.run("RETURN 1").single()
    except Exception as e:
        g.close()
        pytest.skip(f"Neo4j not reachable: {e}")

    yield g

    # cleanup
    with g._get_session() as session:
        session.execute_write(
            lambda tx: tx.run(
                "MATCH (n:Node {graph_id: $gid}) DETACH DELETE n",
                gid=g.graph_id,
            )
        )

    g.close()
