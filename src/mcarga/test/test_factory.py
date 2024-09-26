import pytest

import random
from collections import Counter

import numpy as np

from common.grid import Grid

from mcarga.abstractions.factory import AbstractionFactory
from mcarga.statemachine.graph_abstraction import GraphAbstraction


factory = AbstractionFactory()


###############################################################################

def get_colour_counts(ga):
    counts = Counter()
    for node, obj in ga.items():
        counts[obj.colour] += 1
    return counts


@pytest.fixture
def init_simple():

    grid = [
        [0, 1, 2],
        [1, 2, 0],
        [2, 0, 1]
    ]

    ga = GraphAbstraction(grid)
    print()
    print(grid)
    return ga


@pytest.fixture
def init_medium():
    grid = [
        [0, 1, 0, 2],
        [1, 1, 0, 2],
        [0, 0, 3, 3],
        [4, 0, 3, 0]
    ]

    ga = GraphAbstraction(grid)
    print()
    print(grid)
    return ga


@pytest.fixture
def init_complex():
    # note 2 diagonals for 1 and 3.
    grid = [
        [0, 1, 0, 2, 0],
        [1, 0, 0, 2, 0],
        [0, 0, 3, 3, 0],
        [4, 0, 3, 0, 3],
        [4, 0, 3, 0, 3]
    ]

    ga = GraphAbstraction(grid)

    print()
    print(grid)
    return ga


@pytest.fixture
def init_different_side_grids():
    grid = [
        [0, 1, 1, 2, 2, 2],
        [1, 1, 0, 2, 2, 2],
        [1, 0, 3, 3, 2, 2],
        [0, 3, 3, 3, 0, 0],
        [3, 3, 0, 0, 4, 5]
    ]

    ga = GraphAbstraction(grid)

    assert ga.width == 6
    assert ga.height == 5
    assert ga.background_colour == 0
    assert set(ga.array_1d) == {0, 1, 2, 3, 4, 5}

    print()
    print(grid)

    return ga


def just_check_some_stuff(ga):
    ga2 = GraphAbstraction(ga.original_grid)
    assert ga.width == ga2.width
    assert ga.height == ga2.height
    assert ga.background_colour == ga2.background_colour
    assert len(ga.array_1d) == len(ga2.array_1d)
    assert set(ga.array_1d) == set(ga2.array_1d)
    assert ga.least_common_colour == ga2.least_common_colour
    assert ga.most_common_colour == ga2.most_common_colour

    assert ga.original_grid == ga2.original_grid


def test_init_0(init_simple):
    ga = init_simple
    just_check_some_stuff(ga)


def test_init_1(init_medium):
    ga = init_medium
    just_check_some_stuff(ga)


def test_init_2(init_complex):
    ga = init_complex
    just_check_some_stuff(ga)


def test_init_3(init_different_side_grids):
    ga = init_different_side_grids
    just_check_some_stuff(ga)


################################################################################

# a group of adjacent pixels of the same colour in the original graph, including background colour

def test_scg_simple(init_simple):
    ga = init_simple

    ga = factory.create("scg", ga.original_grid)

    assert len(ga.objs) == 9

    # Check if the colours are correctly assigned
    assert get_colour_counts(ga) == {0: 3, 1: 3, 2: 3}


def test_scg_medium(init_medium):
    ga = init_medium

    ga = factory.create("scg", ga.original_grid)

    assert len(ga.objs) == 8

    # Check if the colours are correctly assigned
    assert get_colour_counts(ga) == {0: 4, 1: 1, 2: 1, 3: 1, 4: 1}

    for ii in ga.indices():
        print(ii)

    for oo in ga.objs:
        print(oo)

    assert ga.width == 4
    assert ga.height == 4


def test_scg_complex(init_complex):
    # note the are 2 diagonals for 1 and 3.  scg treats them as seperate nodes

    ga = init_complex
    ga = factory.create("scg", ga.original_grid)

    assert len(ga.objs) == 10

    # Check if the colours are correctly assigned
    assert get_colour_counts(ga) == {0: 4, 1: 2, 2: 1, 3: 2, 4: 1}


def test_scg_different_side_grids(init_different_side_grids):
    ga = init_different_side_grids
    ga = factory.create("scg", ga.original_grid)

    assert len(ga.objs) == 11

    # Check if the colours are correctly assigned
    assert get_colour_counts(ga) == {0: 6, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1}


################################################################################
# scg_nb - single_connected_graph_no_background()
################################################################################

def test_scg_nb_simple(init_simple):
    ga = init_simple
    ga = factory.create("scg_nb", ga.original_grid)

    assert len(ga.objs) == 6
    assert get_colour_counts(ga) == {1: 3, 2: 3}


def test_scg_nb_medium(init_medium):
    ga = init_medium
    ga = factory.create("scg_nb", ga.original_grid)

    assert len(ga.objs) == 4
    assert get_colour_counts(ga) == {1: 1, 2: 1, 3: 1, 4: 1}


def test_scg_nb_complex(init_complex):
    ga = init_complex
    ga = factory.create("scg_nb", ga.original_grid)

    assert len(ga.objs) == 6
    assert get_colour_counts(ga) == {1: 2, 2: 1, 3: 2, 4: 1}


def test_scg_nb_different_side_grids(init_different_side_grids):
    ga = init_different_side_grids
    ga = factory.create("scg_nb", ga.original_grid)

    assert len(ga.objs) == 5
    assert get_colour_counts(ga) == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}


def test_scg_nb__different_background_colour():
    # note 2 diagonals for 1 and 3.
    grid = [
        [8, 1, 8, 2, 8],
        [1, 8, 8, 2, 8],
        [8, 8, 3, 3, 8],
        [4, 8, 3, 8, 3]
    ]

    ga = GraphAbstraction(grid)
    ga = factory.create("scg_nb", ga.original_grid)

    assert ga.background_colour == 0
    assert len(ga.objs) == 10

    ga = factory.create("scg_nb_dg", ga.original_grid)

    assert ga.background_colour == 0
    assert len(ga.objs) == 6


def test_scg_nb_s2__different_background_colour():
    # note 2 diagonals for 1 and 3.
    grid = [
        [8, 1, 8, 2, 8],
        [1, 8, 8, 2, 8],
        [8, 8, 3, 3, 8],
        [4, 8, 3, 8, 3]
    ]

    ga = GraphAbstraction(grid)
    ga = factory.create("scg_nb_s2", ga.original_grid)

    assert ga.background_colour == 8
    assert len(ga.objs) == 7

    ga = factory.create("scg_nb_s2_dg", ga.original_grid)

    assert ga.background_colour == 8
    assert len(ga.objs) == 4


################################################################################

def test_rest_simple(init_simple):
    grid = init_simple.original_grid

    for name in "scg_nbc scg_nb_s2".split():
        ga = factory.create(name, grid)

        assert ga.background_colour == 0
        # Check the number of nodes in the abstracted graph
        assert len(ga.objs) == 8

        # Check if the colours are correctly assigned
        assert get_colour_counts(ga) == {0: 2, 1: 3, 2: 3}


def test_rest_medium(init_medium):
    grid = init_medium.original_grid

    ga = factory.create("scg_nbc", grid)

    assert ga.background_colour == 0

    # Check the number of nodes in the abstracted graph
    assert len(ga.objs) == 6

    # Check if the colours are correctly assigned
    assert get_colour_counts(ga) == {0: 2, 1: 1, 2: 1, 3: 1, 4: 1}

    ga = factory.create("scg_nb_s2", grid)

    assert ga.background_colour == 0

    # Check the number of nodes in the abstracted graph
    assert len(ga.objs) == 5

    # Check if the colours are correctly assigned
    assert get_colour_counts(ga) == {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}


def test_rest_complex(init_complex):
    grid = init_complex.original_grid

    ga = factory.create("scg_nbc", grid)

    assert ga.background_colour == 0

    # Check the number of nodes in the abstracted graph
    assert len(ga.objs) == 8

    # Check if the colours are correctly assigned
    assert get_colour_counts(ga) == {0: 2, 1: 2, 2: 1, 3: 2, 4: 1}

    ga = factory.create("scg_nb_s2", grid)

    assert ga.background_colour == 0

    # Check the number of nodes in the abstracted graph
    assert len(ga.objs) == 7

    # Check if the colours are correctly assigned
    assert get_colour_counts(ga) == {0: 1, 1: 2, 2: 1, 3: 2, 4: 1}


def test_rest_different_side_grids(init_different_side_grids):

    grid = init_different_side_grids.original_grid

    ga = factory.create("scg_nbc", grid)

    # Check the number of nodes in the abstracted graph
    assert len(ga.objs) == 10

    # Check if the colours are correctly assigned
    assert get_colour_counts(ga) == {0: 5, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1}

    ga = factory.create("scg_nb_s1", grid)

    assert ga.background_colour == 0

    # Check the number of nodes in the abstracted graph
    assert len(ga.objs) == 7

    # Check if the colours are correctly assigned
    assert get_colour_counts(ga) == {0: 2, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1}


###############################################################################
# na - get_no_abstraction_graph()
# noop - one graph, maybe used for Patch XXX  rxe
#
# an abstracted graph where a node is defined as:
#  the entire graph as one multi-colour node.
#
######################################################################

def test_no_abstraction_graph():
    # Create a simple test grid
    grid = [
        [0, 1, 2],
        [1, 2, 0],
        [2, 0, 1]
    ]

    grid = GraphAbstraction(grid).original_grid
    ga = factory.create("na", grid)

    # Check that the graph has only one node
    assert len(ga.objs) == 1
    assert ga.background_colour == 0

    # Get the single node
    ii = ga.indices()[0]
    oo = ga.get_obj(ii)

    # Check node properties
    assert oo.size == 9  # 3x3 grid
    assert oo.colours == {0, 1, 2}
    assert set(oo.as_coords()) == {(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)}

    # Check that the abstraction type is correct
    assert ga.abstraction_type == "na"


def test_no_abstraction_graph_single_colour():
    # Test with a single-colour grid
    import numpy as np
    single_colour_grid = np.full((2, 2), 5).tolist()
    grid = GraphAbstraction(single_colour_grid).original_grid

    ga = factory.create("na", grid)

    assert len(ga.objs) == 1
    ii = ga.indices()[0]
    oo = ga.get_obj(ii)
    assert oo.size == 4
    assert oo.colours == {5}
    assert set(oo.as_coords()) == {(0, 0), (0, 1), (1, 0), (1, 1)}


###############################################################################

def test_vertical_connected_graph_no_background():
    grid = [
        [1, 0, 2, 2],
        [1, 0, 0, 2],
        [1, 3, 0, 2],
        [0, 3, 0, 2]
    ]

    grid = GraphAbstraction(grid).original_grid

    print()
    print(grid)

    ga = factory.create("vcg_nb", grid)

    assert len(ga.objs) == 4

    sizes = [obj.size for obj in ga.objs]
    sizes.sort()
    assert sizes == [1, 2, 3, 4]


def test_get_multicolour_connected_components_graph():
    grid = [
        [0, 1, 2, 0],
        [1, 1, 2, 0],
        [2, 2, 1, 3],
        [0, 3, 3, 3]
    ]

    grid = GraphAbstraction(grid).original_grid

    print()
    print(grid)

    ga = factory.create("mcg_nb", grid)

    # 1 multicolour components
    assert len(ga.objs) == 1
    sizes = [o.size for o in ga.objs]
    assert sizes == [12]


def test_get_multicolour_connected_components_graph2():
    grid = [
        [0, 1, 2, 0, 0, 1],
        [1, 1, 2, 0, 0, 2],
        [2, 2, 1, 3, 0, 3],
        [0, 3, 3, 3, 0, 2]
    ]

    grid = GraphAbstraction(grid).original_grid

    print()
    print(grid)

    ga = factory.create("mcg_nb", grid)

    # 3 multicolour components
    assert len(ga.objs) == 2
    sizes = [o.size for o in ga.objs]
    sizes.sort()
    assert sizes == [4, 12]


def test_abstraction_consistency():
    original_grid = Grid([[0, 1, 2, 0],
                          [1, 1, 2, 0],
                          [2, 2, 1, 3],
                          [0, 3, 3, 3]])

    abstractions = [
        factory.create("scg", original_grid),
        factory.create("scg_nb", original_grid),
        factory.create("scg_nbc", original_grid),
        factory.create("scg_nb_s1", original_grid),
        factory.create("scg_nb_s2", original_grid),
        factory.create("scg_nb_s3", original_grid),
        factory.create("vcg_nb", original_grid),
        factory.create("hcg_nb", original_grid),
        factory.create("mcg_nb", original_grid)
    ]

    for ga in abstractions:
        grid = ga.undo_abstraction()
        assert grid == original_grid

    for name in factory.mapping.keys():
        ga = factory.create(name, original_grid)
        grid = ga.undo_abstraction()
        assert grid == original_grid


def test_large_grid():
    pytest.skip("slow")
    for i in range(5):
        h = random.randint(16, 30)
        w = random.randint(16, 30)
        large_grid = Grid(np.random.randint(0, 5, size=(h, w)))

        for name in factory.mapping.keys():
            ga = factory.create(name, large_grid)
            grid = ga.undo_abstraction()
            assert grid == large_grid


def test_grid_with_all_same_non_zero_colour():
    grid = np.full((5, 5), 3)

    for name in "scg scg_nb scg_nbc scg_nb_s1 scg_nb_s2 scg_nb_s3 mcg_nb vcg_nb hcg_nb".split():
        ga = factory.create(name, grid)

        if name not in "scg scg_nb mcg_nb vcg_nb hcg_nb".split():
            assert ga.background_colour == 3
        assert ga.most_common_colour == 3
        assert ga.all_colours == {3}

        print(name, ga.objs)


def test_grid_with_disconnected_components():
    grid = [
        [1, 0, 1, 0, 1],
        [0, 2, 0, 2, 0],
        [1, 0, 1, 0, 1],
        [0, 2, 0, 2, 0],
        [1, 0, 1, 0, 1]]

    ga = factory.create("scg_nb", grid)

    # 13 disconnected components
    assert len(ga.objs) == 13


def test_abstraction_edge_preservation():
    grid = [[1, 1, 0, 2, 2],
            [1, 1, 0, 2, 2],
            [0, 0, 0, 0, 0],
            [3, 3, 0, 4, 4],
            [3, 3, 0, 4, 4]]

    ga = factory.create("scg_nb", grid)

    def has_edge(index0, index1):
        o0 = ga.get_obj(index0)
        o1 = ga.get_obj(index1)
        return o0.has_edge(o1)

    assert has_edge((1, 0), (2, 0)) == "horizontal"
    assert has_edge((1, 0), (3, 0)) == "vertical"
    assert has_edge((4, 0), (3, 0)) == "horizontal"
    assert has_edge((2, 0), (4, 0)) == "vertical"
    assert has_edge((1, 0), (4, 0)) is None


def test_get_largest_rectangle_graph():
    grid = [
        [1, 1, 1, 0],
        [1, 1, 1, 0],
        [1, 1, 1, 2],
        [0, 0, 2, 2]]

    ga = factory.create("lrg", grid)

    # there are 3 rectangles
    assert len(ga.objs) == 3

    assert get_colour_counts(ga) == {1: 1, 2: 2}

    o = ga.get_obj((1, 0))
    assert o.size == 9

    assert ga.undo_abstraction() == ga.original_grid


def test_get_largest_rectangle_graph2():
    grid = [
        [0, 1, 1, 0],
        [1, 1, 1, 0],
        [2, 1, 1, 2],
        [1, 1, 1, 2]]

    ga = factory.create("lrg", grid)

    # there are 3 rectangles
    assert len(ga.objs) == 5

    assert get_colour_counts(ga) == {1: 3, 2: 2}

    # just happen largest rect defined first
    o = ga.get_obj((1, 0))
    assert o.size == 8

    assert ga.undo_abstraction() == ga.original_grid
