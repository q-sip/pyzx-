from pyzx import VertexType

from pyzx.graph.base import BaseGraph, VT, ET
from pyzx.simplify import pivot_gadget_simp, clifford_simp, gadget_simp, copy_simp, \
    supplementarity_simp, spider_simp, to_gh, id_simp, pivot_simp, lcomp_simp, pivot_boundary_simp, fuse_simp, \
    remove_self_loop_simp


def interior_clifford_simp(g: BaseGraph[VT,ET]) -> bool:
    """Keeps doing the simplifications ``id_simp``, ``spider_simp``,
    ``pivot_simp`` and ``lcomp_simp`` until none of them can be applied anymore."""
    spider_simp(g)
    to_gh(g)
    i = 0
    while True:
        i1 = id_simp(g)
        i2 = spider_simp(g)
        i3 = pivot_simp(g)
        i4 = lcomp_simp(g)
        if not (i1 or i2 or i3 or i4): break
        i += 1
    return i != 0


def full_reduce(g: BaseGraph[VT,ET]) -> None: # pragma: no mutate
    """The main simplification routine of PyZX. It uses a combination of :func:`clifford_simp` and
    the gadgetization strategies :func:`pivot_gadget_simp` and :func:`gadget_simp`. It also attempts to run :func:`supplementarity_simp` and :func:`copy_simp`."""
    if any(g.types()[h] == VertexType.H_BOX for h in g.vertices()):
        raise ValueError("Input graph is not a ZX-diagram as it contains an H-box. "
                         "Maybe call pyzx.hsimplify.from_hypergraph_form(g) first?")
    interior_clifford_simp(g)
    pivot_gadget_simp(g)
    iteration = 0
    while True:
        iteration += 1
        clifford_simp(g)
        i = gadget_simp(g)
        interior_clifford_simp(g)
        k = copy_simp(g)
        l = supplementarity_simp(g)
        j = pivot_gadget_simp(g)
        if not (i or j or k or l):
            g.remove_isolated_vertices()
            break





def full_reduce2(g: BaseGraph[VT,ET]) -> None: # pragma: no mutate
    """The main simplification routine of PyZX. It uses a combination of :func:`clifford_simp` and
    the gadgetization strategies :func:`pivot_gadget_simp` and :func:`gadget_simp`. It also attempts to run :func:`supplementarity_simp` and :func:`copy_simp`."""
    if any(g.types()[h] == VertexType.H_BOX for h in g.vertices()):
        raise ValueError("Input graph is not a ZX-diagram as it contains an H-box. "
                         "Maybe call pyzx.hsimplify.from_hypergraph_form(g) first?")

    ##interior clifford
    # spider_simp(g)
    i = fuse_simp(g)
    j = remove_self_loop_simp(g)

    to_gh(g)
    i = 0
    while True:
        i1 = id_simp(g)
        # i2 = spider_simp(g)
        i2 = fuse_simp(g)
        j = remove_self_loop_simp(g)

        i3 = pivot_simp(g)
        i4 = lcomp_simp(g)
        if not (i1 or i2 or i3 or i4): break
        i += 1


    pivot_gadget_simp(g)
    iteration = 0
    while True:
        iteration += 1

        # clifford_simp(g)
        i = False
        while True:
            # i = interior_clifford_simp(g)
            ##interior clifford
            # spider_simp(g)
            i = fuse_simp(g)
            j = remove_self_loop_simp(g)

            to_gh(g)
            i = 0
            while True:
                i1 = id_simp(g)
                # i2 = spider_simp(g)
                i2 = fuse_simp(g)
                j = remove_self_loop_simp(g)

                i3 = pivot_simp(g)
                i4 = lcomp_simp(g)
                if not (i1 or i2 or i3 or i4): break
                i += 1

            i2 = pivot_boundary_simp(g)
            if not i2:
                break

        i = gadget_simp(g)

        ##interior clifford
        spider_simp(g)
        to_gh(g)
        i = 0
        while True:
            i1 = id_simp(g)
            i2 = spider_simp(g)
            i3 = pivot_simp(g)
            i4 = lcomp_simp(g)
            if not (i1 or i2 or i3 or i4): break
            i += 1



        k = copy_simp(g)
        l = supplementarity_simp(g)
        j = pivot_gadget_simp(g)
        if not (i or j or k or l):
            g.remove_isolated_vertices()
            break



g = BaseGraph




to_gh(g)                                    # yeah done
id_simp(g)
fuse_simp(g)                                # yeah done
remove_self_loop_simp(g)
pivot_simp(g)
lcomp_simp(g)
pivot_boundary_simp(g)
gadget_simp(g)
copy_simp(g)
supplementarity_simp(g)
pivot_gadget_simp(g)
g.remove_isolated_vertices()                # kind a, from the implemented