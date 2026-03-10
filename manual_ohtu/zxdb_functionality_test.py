import os
from dotenv import load_dotenv
import pyzx as zx
from pyzx.graph.zxdb.zxdb import ZXdb
from pyzx.graph.graph_memgraph import GraphMemgraph

load_dotenv()
URI = os.getenv("MEMGRAPH_URI")
AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))
c = zx.generate.CNOT_HAD_PHASE_circuit(2, 20, seed=50)
g = c.to_graph(backend='memgraph')
zxdb = ZXdb(URI, AUTH[0], AUTH[1])
path = zxdb.current_path
def graph_full_reduce():
    zxdb.spider_fusion()
    print('hadamard_cancel')
    zxdb.hadamard_cancel()
    print('remove_identities')
    zxdb.remove_identities()
    print('pivot_rule')
    zxdb.pivot_rule()
    print('local_complementation_rule')
    zxdb.local_complementation_rule()
    print('phase_gadget_fusion_rule')
    zxdb.phase_gadget_fusion_rule()
    print('pivot_gadget_rule')
    zxdb.pivot_gadget_rule()
    print('pivot_boundary_rule')
    zxdb.pivot_boundary_rule()
    print('bialgebra_simp')
    zxdb.bialgebra_simp()
    print('get_degree_distribution')
    zxdb.get_degree_distribution()
    print('turn_hadamard_gates_into_edges')
    zxdb.turn_hadamard_gates_into_edges()


# def heal_graph_ids(g):
#     """Finds nodes created by ZXdb that are missing IDs/properties and assigns them."""
#     with g.driver.session() as session:
#         # 1. Heal missing IDs
#         res = session.run(
#             "MATCH (n:Node {graph_id: $graph_id}) RETURN max(n.id) as max_id", 
#             graph_id=g.graph_id
#         ).single()
#         max_id = res["max_id"] if res and res["max_id"] is not None else -1
        
#         query = """
#         MATCH (n:Node {graph_id: $graph_id})
#         WHERE n.id IS NULL
#         RETURN id(n) AS internal_id
#         """
#         missing_records = session.run(query, graph_id=g.graph_id)
#         missing_ids = [record["internal_id"] for record in missing_records]
        
#         for internal_id in missing_ids:
#             max_id += 1
#             session.run(
#                 "MATCH (n) WHERE id(n) = $int_id SET n.id = $new_id", 
#                 int_id=internal_id, 
#                 new_id=max_id
#             )
            
#         if missing_ids:
#             print(f"HEALED: Assigned valid IDs to {len(missing_ids)} ghost nodes.")

#         # 2. Heal missing layout coordinates (qubit / row)
#         session.run("MATCH (n:Node {graph_id: $graph_id}) WHERE n.qubit IS NULL SET n.qubit = 0", graph_id=g.graph_id)
#         session.run("MATCH (n:Node {graph_id: $graph_id}) WHERE n.row IS NULL SET n.row = 0", graph_id=g.graph_id)
        
#         # PyZX sometimes uses 'q' and 'r' as shorthand in graph databases
#         session.run("MATCH (n:Node {graph_id: $graph_id}) WHERE n.q IS NULL SET n.q = 0", graph_id=g.graph_id)
#         session.run("MATCH (n:Node {graph_id: $graph_id}) WHERE n.r IS NULL SET n.r = 0", graph_id=g.graph_id)
#         print("HEALED: Filled in missing layout coordinates.")

for x in range(100):
    graph_full_reduce()

#heal_graph_ids(g)

# 2. Now PyZX can safely read it
g.normalize()

# 3. Copy the graph to local memory (Simple backend) so the tensor calculation
# doesn't have to send 10,000 queries to Memgraph, which takes forever.
g_local = g.copy(backend='simple')

# 4. Compare the reduced graph directly to the original circuit!
print(f'Comparing: {zx.compare_tensors(g_local, c, preserve_scalar=False)}')