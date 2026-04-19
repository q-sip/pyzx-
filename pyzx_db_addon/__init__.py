"""PyZX database backend addon."""

from __future__ import annotations

from typing import Any, Optional

import pyzx
import pyzx.graph.graph as pyzx_graph

from .graph_AGE import GraphAGE
from .graph_memgraph import GraphMemgraph
from .graph_neo4j import GraphNeo4j

_BACKEND_FACTORIES: dict[str, type[Any]] = {
	"age": GraphAGE,
	"apache age": GraphAGE,
	"apache_age": GraphAGE,
	"postgres": GraphAGE,
	"postgresql": GraphAGE,
	"neo4j": GraphNeo4j,
	"memgraph": GraphMemgraph,
}

_original_module_graph = pyzx_graph.Graph
_original_top_level_graph = getattr(pyzx, "Graph", _original_module_graph)


def _normalize_backend(backend: Any) -> Optional[str]:
	if backend is None:
		return None
	return str(backend).strip().lower()


def create_graph(backend: Any = None, **kwargs: Any) -> Any:
	"""Create a graph using addon backends when known, otherwise delegate to PyZX."""
	normalized = _normalize_backend(backend)
	factory = _BACKEND_FACTORIES.get(normalized or "")
	if factory is not None:
		return factory(**kwargs)
	return _original_module_graph(backend=backend, **kwargs)


def _patched_graph(backend: Any = None, **kwargs: Any) -> Any:
	return create_graph(backend=backend, **kwargs)


def enable_pyzx_backend_overrides() -> None:
	"""Patch PyZX so Graph(..., backend='age'|'neo4j'|'memgraph') uses addon backends."""
	pyzx_graph.Graph = _patched_graph
	pyzx.Graph = _patched_graph


def disable_pyzx_backend_overrides() -> None:
	"""Restore PyZX's original Graph factory/class."""
	pyzx_graph.Graph = _original_module_graph
	pyzx.Graph = _original_top_level_graph


def __getattr__(name: str) -> Any:
	if name == "ZXdb":
		from .zxdb import ZXdb

		return ZXdb
	if name == "ZXdbAge":
		from .zxdb_age import ZXdbAge

		return ZXdbAge
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
	"GraphAGE",
	"GraphNeo4j",
	"GraphMemgraph",
	"ZXdb",
	"ZXdbAge",
	"create_graph",
	"enable_pyzx_backend_overrides",
	"disable_pyzx_backend_overrides",
]
