import pytest

from common.grid import Grid

from mcarga.abstractions.factory import AbstractionFactory
from mcarga.statemachine.graph_abstraction import GraphAbstraction


factory = AbstractionFactory()


def test_simple_objects():
    # 3 objects in this grid
    # - two in the middle touching
    # - one in the bottom right corner, isolated
    sample_grid = [
        [0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 1]
        ]

    grid = Grid(sample_grid)
    ga = factory.create("scg_nb", grid)

    assert ga.abstraction_type == "scg_nb"

    assert len(ga.objs) == 3

    # this isnnt coord
    indices = [(x, y) for x, y in ga.indices()]

    # this is color, and an index starting from 0
    assert set(indices) == set([(1, 0), (1, 1), (2, 0)])


def test_graph_abstractions_1():
    sample_grid = [
        [0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 1]
        ]

    grid = Grid(sample_grid)
    scg = factory.create("scg", grid)
    scg_nb = factory.create("scg_nb", grid)

    assert len(scg.objs) == 4
    assert len(scg_nb.objs) == 3

    # simple background - so all the same scg_nb
    scg_nbc = factory.create("scg_nbc", grid)
    scg_nb_s1 = factory.create("scg_nb_s1", grid)
    scg_nb_s2 = factory.create("scg_nb_s2", grid)
    scg_nb_s3 = factory.create("scg_nb_s3", grid)

    assert len(scg_nbc.objs) == 3
    assert len(scg_nb_s1.objs) == 3
    assert len(scg_nb_s2.objs) == 3
    assert len(scg_nb_s3.objs) == 3


def test_line_abstractions_1():
    sample_grid = [
        [1, 0, 0, 0, 0, 0],
        [1, 0, 1, 1, 0, 0],
        [3, 0, 0, 1, 1, 0],
        [3, 2, 2, 2, 1, 1],
        [3, 0, 0, 0, 0, 1]
        ]

    grid = Grid(sample_grid)

    # vertical and horizontal objects
    vcg_nb = factory.create("vcg_nb", sample_grid)
    hcg_nb = factory.create("hcg_nb", sample_grid)

    assert len(vcg_nb.objs) == 9
    assert len(hcg_nb.objs) == 10

    assert sum(o.size for o in vcg_nb.objs) == 15
    assert sum(o.size for o in hcg_nb.objs) == 15

    assert sum(o.size for o in vcg_nb.objs if o.colour == 1) == 9
    assert sum(o.size for o in hcg_nb.objs if o.colour == 1) == 9

    assert sum(o.size for o in vcg_nb.objs if o.colour == 2) == 3
    assert sum(o.size for o in hcg_nb.objs if o.colour == 2) == 3

    assert sum(o.size for o in vcg_nb.objs if o.colour == 3) == 3
    assert sum(o.size for o in hcg_nb.objs if o.colour == 3) == 3


