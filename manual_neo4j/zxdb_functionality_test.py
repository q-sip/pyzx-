import os
from dotenv import load_dotenv
import pyzx as zx
from pyzx.graph.zxdb.zxdb import ZXdb
from pyzx.graph.graph_memgraph import GraphMemgraph

load_dotenv()
URI = os.getenv("MEMGRAPH_URI")
AUTH = (os.getenv("MEMGRAPH_USER"), os.getenv("MEMGRAPH_PASSWORD"))
zxdb = ZXdb(URI, AUTH[0], AUTH[1])
path = zxdb.current_path
def graph_full_reduce():
    zxdb.spider_fusion(graph_id='graph_test_zxdb')

graph_full_reduce()
