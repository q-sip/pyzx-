MATCH (n:Node)-[r:Wire {t:2}]-()
WHERE n.phase
//        -[r:Wire {t:2}]-(m:Node)



RETURN *;








//def check_pivot(
//g: BaseGraph[VT,ET],
//v: VT,
//w: VT
//) -> bool:
//"""Checks if an edge can be simplified using the pivot rule.
//
//    :param g: An instance of a ZX-graph.
//    :param v: The source vertex of the edge to check.
//    :param w: The target vertex of the edge  to check.
//    """
//
//types = g.types()
//phases = g.phases()
//if not (v in g.vertices() and w in g.vertices()): return False                Osa graafia check
//if not g.connected(v, w): return False                                        pitää olla yhtenäinen
//
//if g.edge_type(g.edge(v, w)) != EdgeType.HADAMARD: return False               ainoostaan hadamard yhteyksiä
//
//if not (types[v] == VertexType.Z and types[w] == VertexType.Z): return False  ainotaan z spidereilla
//
//v0a = phases[v]
//v1a = phases[w]
//if not ((v0a in (0,1)) and (v1a in (0,1))): return False                      kumpikaan ei saa olla boundary?
//if g.is_ground(v) or g.is_ground(w):                                          kumpikaan ei saa olla ground
//return False
//
//maybe_v0b = boundary_list_for_vertex(g, v)                                    onko kukaan v naapuri boundary
//if maybe_v0b is None: return False                                            jos kukaan naapuri ei oo boundary nii pois
//b0: List[VT] = maybe_v0b
//
//maybe_v1b = boundary_list_for_vertex(g, w)                                    onko kukaan w naapuri boundary
//if maybe_v1b is None: return False                                            jos kukaan naapuri ei oo boundary nii pois
//b1: List[VT] = maybe_v1b
//
//return len(b0) + len(b1) <= 1                                                 jos v,w naapurustossa oli maksimissaan 1 boundary node