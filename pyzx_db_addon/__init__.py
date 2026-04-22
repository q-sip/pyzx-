"""PyZX database backend addon."""

from __future__ import annotations

import sys
from typing import Any, List, Optional, Tuple

import pyzx
import pyzx.graph.graph as pyzx_graph
# Preload submodules that do `from .graph import Graph`, so force_backend()
# can rebind their already-resolved `Graph` attribute.
import pyzx.generate  # noqa: F401
import pyzx.simplify  # noqa: F401
import pyzx.circuit  # noqa: F401

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
        import pyzx
        import pyzx.graph.graph as pyzx_graph
        pyzx_graph.Graph = _patched_graph
        pyzx.Graph = _patched_graph
        
        # Explicit patching for known PyZX module paths that hard-import Graph
        import pyzx.circuit.graphparser
        import pyzx.simplify
        pyzx.circuit.graphparser.Graph = _patched_graph
        if hasattr(pyzx.simplify, "Graph"):
            pyzx.simplify.Graph = _patched_graph
            
        if hasattr(pyzx_graph, "backends"):
            for b in _BACKEND_FACTORIES.keys():
                pyzx_graph.backends[b] = True

def disable_pyzx_backend_overrides() -> None:
	"""Restore PyZX's original Graph factory/class."""
	pyzx_graph.Graph = _original_module_graph
	pyzx.Graph = _original_top_level_graph


def force_backend(backend: Any) -> List[Tuple[Any, str, Any]]:
	"""Rebind every `Graph` attribute in loaded pyzx.* modules that points
	at PyZX's original Graph to the chosen backend class, so calls like
	`pyzx.generate.cliffordT(...)` produce graphs in that backend.

	Returns an undo list to pass to `restore_backend`.
	"""
	normalized = _normalize_backend(backend)
	factory = _BACKEND_FACTORIES.get(normalized or "")
	if factory is None:
		raise ValueError(f"unknown backend: {backend!r}")
	undo: List[Tuple[Any, str, Any]] = []
	for name, mod in list(sys.modules.items()):
		if not name.startswith("pyzx") or mod is None:
			continue
		for attr in vars(mod):
			try:
				val = getattr(mod, attr)
			except Exception:
				continue
			if val is _original_module_graph:
				setattr(mod, attr, factory)
				undo.append((mod, attr, val))
	return undo


def restore_backend(undo: List[Tuple[Any, str, Any]]) -> None:
	"""Undo a previous `force_backend` call."""
	for mod, attr, old in undo:
		setattr(mod, attr, old)


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
	"force_backend",
	"restore_backend",
]
