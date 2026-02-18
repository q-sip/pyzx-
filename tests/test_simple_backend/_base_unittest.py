# tests/test_simple_backend/_base_unittest.py
import os
import unittest
import uuid

from pyzx.graph.graph_s import GraphS


def _ensure_phase_to_str_exists() -> None:
    # Safety patch for older forks/branches.
    if not hasattr(GraphS, "_phase_to_str"):

        def _phase_to_str(_, phase):
            return "0" if phase is None else str(phase)

        setattr(GraphS, "_phase_to_str", _phase_to_str)

class SimpleUnitTestCase(unittest.TestCase):
    """
    Base for unittests for the simple backend
    """

    def setUp(self):
        _ensure_phase_to_str_exists()

        self.graph_id = f"test_graph_{uuid.uuid4().hex}"
        self.g = GraphS()

    def tearDown(self):
        try:
            self.g.close()
        except Exception:
            pass
