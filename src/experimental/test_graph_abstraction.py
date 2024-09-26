import numpy as np
from common.grid import Grid

from .gabstraction import PatternObject, copy_object, GraphAbstraction, Builder


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



def get_no_abstraction_graph(ga: GraphAbstraction):
    builder = Builder(ga)

    # entire grid is one object
    colour_coords = []
    for i, row in enumerate(ga.original_grid):
        for j, value in enumerate(row):
            pixel = ga.original_grid[i, j]
            colour_coords.append((pixel, (i, j)))

    builder.create_multicolour_obj(colour_coords)

    return builder


def test_bounding_box():
    grid = [[0, 0, 3, 0, 0],
            [0, 1, 1, 1, 0],
            [3, 1, 0, 1, 3],
            [0, 1, 1, 1, 0],
            [0, 0, 3, 0, 0]]

    grid = Grid(grid)
    ga = GraphAbstraction(grid, abstraction_type="lala")
    get_no_abstraction_graph(ga)

    assert ga.get_obj((25, 0)).bounding_box() == (0, 0, 5, 5)

    assert grid == ga.undo_abstraction()


def get_scg_nb(ga: GraphAbstraction, do_diagonals=False):
    builder = Builder(ga)

    from mcarga.abstractions.factory import connected_objects_uni
    for colour, coords in connected_objects_uni(ga.original_grid,
                                                do_diagonals=do_diagonals,
                                                bg_colour=ga.background_colour):
        builder.create_unicolour_obj(coords, colour)

    return builder


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
    ga = GraphAbstraction(grid, abstraction_type="scg_nb")
    get_scg_nb(ga)

    assert ga.abstraction_type == "scg_nb"

    assert len(ga.objs) == 3

    # this isnnt coord
    indices = [(x, y) for x, y in ga.indices()]

    # this is color, and an index starting from 0
    assert set(indices) == set([(1, 0), (1, 1), (2, 0)])

    assert grid == ga.undo_abstraction()
