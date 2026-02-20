"""
Docstring for pyzx.graph.graph_AGE
"""

import os
import uuid
from fractions import Fraction
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

# testing pylint
from dotenv import load_dotenv
#To be replaced
#from neo4j import GraphDatabase

from pyzx.symbolic import new_var, parse
from .graph_db_rewrite_runner import run_rewrite

from ..utils import (
    EdgeType,
    FloatInt,
    FractionLike,
    VertexType,
    vertex_is_zx_like,
    vertex_is_z_like,
    set_z_box_label,
    get_z_box_label,
)
from .base import BaseGraph, upair

load_dotenv()

VT = int
ET = Tuple[int, int]
