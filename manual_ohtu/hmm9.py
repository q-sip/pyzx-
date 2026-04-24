import pyzx as px
from pyzx.graph.graph_memgraph import GraphMemgraph


def delete_all(g: GraphMemgraph):
    query = """MATCH (n) DETACH DELETE n;"""
    g.arb_quer_write(query=query)


def arb_write(g: GraphMemgraph):
    query = """
    MATCH (n:Node)-[r:Wire]-(m:Node) 
    WHERE n.t = 2 
    AND n.graph_id = "graph_test_zxdb"
    SET n.t = 1
    WITH r AS wire
    SET wire.t = CASE WHEN wire.t = 1 THEN 2 ELSE 1 END
    RETURN wire;
    """
    g.arb_quer_write(query=query, kala="koira", kissa="mieto")


def bonus_nodet(g: GraphMemgraph):
    query = """
    CREATE (n:Node)
    SET n.kala = 1
    with *
    MATCH (m:Input)
    CREATE (n) -[r:Wire]->(m)
    SET r.kala = 1;
    """
    g.arb_quer_write(query=query)

def bonus_nodet_end(g: GraphMemgraph):
    query = """
    CREATE (n2:Node)
    SET n2.kala = 1
    with *
    MATCH (m2:Output)
    CREATE (m2)-[r2:Wire]->(n2)
    SET r2.kala = 1;
    """
    g.arb_quer_write(query=query)


iterer = 83
qubit = 2
depth = 3
p_had: float = 0.3
p_t: float = 0.6
seed: int = 7
clifford: bool = False
backend = "memgraph"
# backend = "simple"
no_hadamard = False
internal = 2

g = GraphMemgraph()
delete_all(g)


if internal == 0:
    c = px.generate.CNOT_HAD_PHASE_circuit(qubits=qubit, depth=depth, p_had=p_had, p_t=p_t, seed=seed, clifford=clifford)
    g = c.to_graph(backend=backend)
elif internal == 1:
    g = px.generate.cliffordT(qubits=qubit, depth=depth, p_t=p_t, backend=backend, seed=seed)
elif internal == 2:
    g = px.generate.cliffords(qubits=qubit, depth=depth, no_hadamard=no_hadamard, backend=backend, seed=seed)

try:
    px.full_reduce(g)

    # print(f"iter: {iter}", end='\n')
    # iter += 1
    pass
except ValueError as e:
    print(f"e:", end='\n')
    print(e)

# g2 = g.copy(backend="memgraph")
bonus_nodet(g)
bonus_nodet_end(g)

print(f"iter: {iterer}", end='\n')
print(f"qubit {qubit}", end='\n')
print(f"depth {depth}", end='\n')
print(f"p_had: {p_had}", end='\n')
print(f"p_t: {p_t}", end='\n')
print(f"seed: {seed}", end='\n')
print(f"clifford: {clifford}", end='\n')

# px.draw(g)

# g.torni()
