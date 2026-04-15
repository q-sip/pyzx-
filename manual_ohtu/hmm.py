import pyzx as px
from pyzx import VertexType, EdgeType
from pyzx.graph.graph_memgraph import GraphMemgraph


def holder1():
    g = GraphMemgraph()
    vertices_data = [
        {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 0},
        {"ty": VertexType.X, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 1},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 2},
        {"ty": VertexType.Z, "qubit": 0, "row": 2, 'phsae': 2},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 1},
        {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 4},
    ]
    edges_data = [
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.SIMPLE),
        ((1, 3), EdgeType.SIMPLE),
        ((3, 4), EdgeType.HADAMARD),
        ((3, 5), EdgeType.SIMPLE),
        ((5, 6), EdgeType.SIMPLE),
        ((6, 7), EdgeType.SIMPLE),
    ]
    g.create_graph(vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[7])


def creator1(g: GraphMemgraph):
    vertices_data = [
        {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 0},
        {"ty": VertexType.X, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 1},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 2},
        {"ty": VertexType.Z, "qubit": 0, "row": 2, 'phsae': 2},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 1},
        {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 4},
    ]
    edges_data = [
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.SIMPLE),
        ((1, 3), EdgeType.SIMPLE),
        ((3, 4), EdgeType.HADAMARD),
        ((3, 5), EdgeType.SIMPLE),
        ((5, 6), EdgeType.SIMPLE),
        ((6, 7), EdgeType.SIMPLE),
    ]
    g.create_graph(vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[7])
    pass


def creator2(g: GraphMemgraph):
    c = px.generate.CNOT_HAD_PHASE_circuit(2, 20, seed=50)
    g2 = c.to_graph()
    json = g2.to_json()
    g.from_json(json)


def creator3(g: GraphMemgraph):
    c = px.generate.cliffords(qubits=2, depth=20, seed=50, backend='simple', t_gates=True)
    # g2 = c.to_json()
    # json = g2.to_json()
    g.from_json(c.to_json())


def creator4(g: GraphMemgraph):
    c = px.generate.cliffordT(2, 20, seed=50)
    json = c.to_json()
    g.from_json(json)


def creator5(g: GraphMemgraph):
    vertices_data = [
        {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 0},
        {"ty": VertexType.X, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 1},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 2},
        {"ty": VertexType.Z, "qubit": 0, "row": 2, 'phsae': 2},
        {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 1},
        {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 4},
    ]
    edges_data = [
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.SIMPLE),
        ((1, 3), EdgeType.SIMPLE),
        ((3, 4), EdgeType.HADAMARD),
        ((3, 5), EdgeType.SIMPLE),
        ((5, 6), EdgeType.SIMPLE),
        ((6, 7), EdgeType.SIMPLE),
    ]
    g.create_graph(vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[7])


def arb_write(g: GraphMemgraph):
    query = """
    MATCH (n:Node)-[r:Wire]-(m:Node) 
    WHERE n.t = 2 
    AND n.graph_id = "graph_test_zxdb"
    SET n.t = 1
    WITH DISTINCT r AS wire
    SET wire.t = CASE WHEN wire.t = 1 THEN 2 ELSE 1 END
    RETURN wire;
    """
    g.arb_quer_write(query=query, kala="koira", kissa="mieto")


def maini(g: GraphMemgraph):
    looper = True
    g.remove_all_data()
    data_hold = g.clone()
    while looper:
        print(f"", end='\n')
        print(f"1: create", end='\n')
        print(f"-1: remove", end='\n')
        print(f"2: pyzx debug full reduce", end='\n')
        print(f"draw: to draw", end='\n')
        print(f"3: to see if it is graph like", end='\n')
        print(f"4: To graph like", end='\n')
        print(f"5: create cnot had phase", end='\n')
        print(f"6: create Cliffords thing", end='\n')
        print(f"7: create cliffordT", end='\n')
        print(f"8: create again", end='\n')
        print(f"11: to_gh", end='\n')
        print(f"10: clone data to hold", end='\n')
        print(f"12: compare to hold", end='\n')
        print(f"q: quit", end='\n')

        choice = input("Enter your choice: ")
        if choice == "1":
            creator1(g)
        if choice == "-1":
            g.remove_all_data()
        if choice == "2":
            px.simplify.full_reduce(g)
        if choice == "draw" or choice.startswith("d"):
            px.draw(g=g, labels=True)
        if choice == "q":
            looper = False
        if choice == "4":
            px.to_graph_like(g)
        if choice == "3" or choice == "4":
            print(f"is graph-like?: {px.is_graph_like(g)}", end='\n')
        if choice == "5":
            creator2(g)
        if choice == "6":
            creator3(g)
        if choice == "7":
            creator4(g)
        if choice == "8":
            creator5(g)
        if choice == "11":
            px.to_gh(g)
        if choice == "10":
            data_hold = g.clone()
        if choice == "12":
            arvo = px.compare_tensors(g, data_hold, preserve_scalar=True)
            print(f"arvo: {arvo}", end='\n')
        if choice == "13":
            arb_write(g)

        print(f"Command {choice} done", end='\n')

    # g.remove_all_data()
    print(f"Done!", end='\n')


g = GraphMemgraph()
maini(g)
# try:
#     maini(g)
# except Exception as e:
#     print(f"Errored", end='\n')
#     print(f"{e}", end='\n')
#     g.remove_all_data()
