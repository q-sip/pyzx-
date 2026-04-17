from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType, EdgeType
from tests.test_graph_age import test_add_vertices
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fractions import Fraction
import pyzx as zx
import os


g = GraphAGE()
#vertices = g.add_vertices(3)
def manually_constructing():
    i = g.add_vertex(0,0,0)
    v = g.add_vertex(1,0,1, Fraction(1,2))
    w = g.add_vertex(2,0,2, Fraction(-1,2))
    o = g.add_vertex(0,0,3)
    g.add_edges([(i,v), (v,w),(w,o)])

def simplify():
    g = zx.generate.cliffordT(3,20)
    #zx.simplify.full_reduce(g)
    #g.normalise()
    return g

def draw_graph(g):

    vertices = g.get_vertices()
    edges = g.get_edges()

    G = nx.Graph()
    G.add_nodes_from(vertices)
    G.add_edges_from(edges)
    print(G)
    plt.figure()
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=600, font_size=12, edge_color='gray')
    plt.savefig(os.path.abspath("graphs/graph.png"))
    plt.show()

def show_graph():
    G = nx.Graph()
    vertices = g.get_vertices()
    edges = g.get_edges()
    G.add_nodes_from(vertices)
    G.add_edges_from(edges)
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True)
    plt.show()
    
manually_constructing()
#graph=simplify()
show_graph()

#g.delete_graph()
