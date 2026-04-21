import fractions



import pyzx as px
from pyzx import VertexType, EdgeType
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


current_iteration = 0
qubit = 1
depth = 1
p_had: float = 0.2
p_t: float = 0.2
seed: int = 0
clifford: bool = False
# backend = "memgraph"
backend = "simple"
no_hadamard = True
internal = 0



g = GraphMemgraph()
try:
    for qubit in range(2,10):
        for depth in range(1,800):
            for seed in range(0,20):
                for internal in range(0,3):
                    # delete_all(g)
                    clifford = current_iteration % 2 == 0
                    p_had = (current_iteration % 10) / 10
                    p_t = (current_iteration % 11) / 10
                    no_hadamard = current_iteration % 13 == 0
                    if internal == 0:
                        c = px.generate.CNOT_HAD_PHASE_circuit(qubits=qubit,
                                                               depth=depth,
                                                               p_had=p_had,
                                                               p_t=p_t,
                                                               seed=seed,
                                                               clifford=clifford)
                        g = c.to_graph(backend=backend)
                    elif internal == 1:
                        g = px.generate.cliffordT(qubits=qubit,depth=depth,p_t=p_t,backend=backend, seed=seed)
                    elif internal == 2:
                        g = px.generate.cliffords(qubits=qubit, depth=depth, no_hadamard=no_hadamard, backend=backend, seed=seed)

                    px.full_reduce(g)

                    # print(f"iter: {iter}", end='\n')
                    current_iteration += 1

except Exception as e:
    print(f"e:", end='\n')
    print(e)

print(f"iter: {current_iteration}", end='\n')
print(f"qubit: {qubit}", end='\n')
print(f"depth: {depth}", end='\n')
print(f"p_had: {p_had}", end='\n')
print(f"p_t: {p_t}", end='\n')
print(f"seed: {seed}", end='\n')
print(f"clifford: {clifford}", end='\n')
print(f"internal: {internal}", end='\n')
print(f"no_hadamard: {no_hadamard}", end='\n')



