import numpy as np
import pytest

from mcarga.statemachine.graph_abstraction import GraphAbstraction
from mcarga.abstractions.factory import AbstractionFactory

from mcarga.core import utils

from collections import Counter


def test_ga_initialization():
    simple_grid = [
        [0, 1, 0],
        [1, 2, 0],
        [2, 0, 0],
        [0, 3, 0]
    ]

    just_checking = np.array(simple_grid)
    ga = GraphAbstraction(simple_grid)

    assert just_checking.shape == ga.original_grid.shape
    assert just_checking.shape == ga.shape
    assert ga.shape == (4, 3)

    assert ga.width == 3
    assert ga.height == 4
    assert ga.background_colour == 0

    assert len(ga.array_1d) == 3 * 4
    assert set(ga.array_1d) == {0, 1, 2, 3}


def test_ga_initialization_complex():
    grid = [
        [0, 1, 1, 2, 2],
        [1, 1, 0, 2, 1],
        [1, 0, 3, 3, 1],
        [0, 3, 1, 3, 0],
        [3, 3, 0, 0, 4]
    ]

    ga = GraphAbstraction(grid)
    assert ga.width == 5
    assert ga.height == 5
    assert len(ga.array_1d) == 25
    assert set(ga.array_1d) == {0, 1, 2, 3, 4}
    assert ga.background_colour == 0
    assert ga.least_common_colour == 4
    assert ga.most_common_colour == 1

    assert 4, 4 in ga.corners
    assert ga.corners == ga.corners


@pytest.mark.xfail(raises=AssertionError)
def test_empty_grid():
    empty_grid = [[]]
    ga = GraphAbstraction(empty_grid)


def test_bounding_box():
    grid = [[0, 0, 3, 0, 0],
            [0, 1, 1, 1, 0],
            [3, 1, 0, 1, 3],
            [0, 1, 1, 1, 0],
            [0, 0, 3, 0, 0]]

    f = AbstractionFactory()
    ga = f.create("scg_nb", grid)

    assert ga.get_obj((1, 0)).bounding_box() == (1, 1, 3, 3)
