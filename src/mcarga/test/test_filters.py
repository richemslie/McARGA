import pytest

from competition import loader
from competition.runner import show_task

from common.grid import Grid

from mcarga.abstractions.factory import AbstractionFactory, GraphBundle

from mcarga.gen_values import PossibleValuesFilters
from mcarga.selection.filters import Filters
from mcarga.selection import filters


def create_ga(g, abstraction="scg_nb"):
    grid = Grid(g)
    ga = AbstractionFactory().create(abstraction, grid)
    filters = Filters(ga)
    return ga, filters


def test_filter_by_colour():
    sample_grid = [
        [0, 1, 1, 0, 2],
        [0, 1, 2, 0, 2],
        [0, 2, 2, 0, 2],
        [3, 3, 0, 0, 0],
        [3, 3, 0, 0, 0]]

    ga, filters = create_ga(sample_grid)

    # Test basic colour filtering
    assert filters.by_colour((1, 0), 1)
    assert filters.by_colour((2, 0), 2)
    assert filters.by_colour((3, 0), 3)
    assert not filters.by_colour((2, 1), 1)

    # Test exclusion
    assert filters.by_colour((1, 0), 2, exclude=True)
    assert not filters.by_colour((1, 0), 1, exclude=True)

    assert ga.most_common_colour == 2
    assert ga.least_common_colour == 1

    assert filters.by_colour((2, 0), "most")
    assert filters.by_colour((1, 0), "least")

    # Test with non-existent colour
    assert not filters.by_colour((1, 0), 5)


def test_filter_by_size():
    sample_grid = [
        [0, 1, 1, 0, 2],
        [0, 1, 2, 0, 2],
        [0, 2, 2, 0, 2],
        [3, 3, 0, 0, 0],
        [3, 3, 0, 0, 0]]

    ga, filters = create_ga(sample_grid)

    # Size of colour 1 component
    assert filters.by_size((1, 0), 3)

    # Test exclusion
    assert filters.by_size((1, 0), 4, exclude=True)

    # Test with 'max' and 'min' sizes
    assert filters.by_size((3, 0), "max")

    # two has minimum size
    assert filters.by_size((1, 0), "min")
    assert filters.by_size((2, 0), "min")

    # Test odd/even sizes
    assert filters.by_size((1, 0), "odd")
    assert filters.by_size((3, 0), "odd", exclude=True)


def test_filter_by_neighbour_size():
    sample_grid = [
        [1, 1, 1, 0, 2],
        [0, 1, 2, 2, 2],
        [0, 2, 2, 0, 2],
        [3, 0, 0, 0, 0],
        [3, 0, 0, 0, 0]]

    ga, filters = create_ga(sample_grid)

    # Test basic neighbour size filtering
    assert filters.by_neighbour_size((2, 0), 4)
    assert filters.by_neighbour_size((1, 0), 7)

    # Test with 'max' and 'min' neighbour sizes
    assert filters.by_neighbour_size((1, 0), "max")
    assert filters.by_neighbour_size((1, 0), "min")

    # Test odd/even neighbour sizes
    assert filters.by_neighbour_size((1, 0), "odd")

    # Assuming colour 3 has no neighbours
    assert not filters.by_neighbour_size((2, 0), "odd")


def test_filter_by_neighbour_colour():
    sample_grid = [
        [0, 1, 1, 0, 2],
        [0, 1, 2, 0, 2],
        [0, 2, 2, 0, 2],
        [3, 3, 0, 0, 0],
        [3, 3, 0, 0, 0]]

    ga, filters = create_ga(sample_grid)

    # Test basic neighbour colour filtering
    assert filters.by_neighbour_colour((1, 0), 2)
    assert not filters.by_neighbour_colour((1, 0), 3)

    # Test with 'same' colour
    assert not filters.by_neighbour_colour((1, 0), "same")

    assert filters.by_neighbour_colour((2, 0), "same")

    # Test with 'most' and 'least' common colours
    assert filters.by_neighbour_colour((2, 0), "most")
    assert not filters.by_neighbour_colour((1, 0), "least")


def test_multiple_filters():
    sample_grid = [
        [0, 1, 1, 0, 2],
        [0, 1, 2, 0, 2],
        [0, 2, 2, 0, 2],
        [3, 3, 0, 0, 0],
        [3, 3, 0, 0, 0]]

    ga, filters = create_ga(sample_grid)

    # Test combination of filters
    assert filters.by_colour((1, 0), 1) and filters.by_size((1, 0), 3)
    assert filters.by_colour((2, 0), 2) and filters.by_neighbour_colour((2, 0), 1)


def test_filters_with_multicolour_abstraction():
    sample_grid = [
        [0, 1, 1, 0, 2],
        [0, 1, 2, 0, 2],
        [0, 2, 2, 0, 2],
        [3, 3, 0, 0, 0],
        [3, 3, 0, 0, 0]]

    ga, filters = create_ga(sample_grid, abstraction="mcg_nb")

    # Test colour filtering in multicolour graph
    assert filters.by_colour((10, 0), 1)
    assert filters.by_colour((10, 0), 2)
    assert not filters.by_colour((10, 0), 0)

    # Test size filtering in multicolour graph
    assert filters.by_size((10, 0), 10)

    # Test neighbour filtering in multicolour graph
    assert not filters.by_neighbour_size((3, 0), 5)


def test_filters_edge_cases():
    sample_grid = [
        [0, 1, 1, 0, 2],
        [0, 1, 2, 0, 2],
        [0, 2, 2, 0, 2],
        [3, 3, 0, 0, 0],
        [3, 3, 0, 0, 0]]

    ga, filters = create_ga(sample_grid)

    # Test with non-existent node
    with pytest.raises(KeyError):
        filters.by_colour((10, 0), 1)

    # Test with invalid colour
    assert not filters.by_colour((1, 0), 10)

    # Test with invalid size
    assert not filters.by_size((1, 0), 100)


def test_filters_with_empty_graph():
    empty_grid = [[0, 0], [0, 0]]

    ga, filters = create_ga(empty_grid, abstraction="scg")

    # All filters should return False for empty graph
    assert not filters.by_colour((0, 0), 1)
    assert not filters.by_size((0, 0), 1)

    assert not filters.by_neighbour_size((0, 0), 1)
    assert not filters.by_neighbour_colour((0, 0), 1)


def test_similar_shapes():
    sample_grid = [
        [0, 1, 1, 2, 2],
        [0, 1, 0, 2, 0],
        [0, 1, 0, 2, 0],
        [3, 0, 0, 0, 0],
        [3, 3, 0, 0, 2]]

    ga, filters = create_ga(sample_grid)

    '''
    ((3, 0), ArcObject(cords: [(4, 0), (3, 0), (4, 1)], colour: 3, #edges 2))
    ((1, 0), ArcObject(cords: [(0, 1), (1, 1), (0, 2), (2, 1)], colour: 1, #edges 2))
    ((2, 0), ArcObject(cords: [(0, 3), (0, 4), (2, 3), (1, 3)], colour: 2, #edges 2))
    ((2, 1), ArcObject(cords: [(4, 4)], colour: 2, #edges 2))

    (1, 0) and (2, 0) are same
    (2, 1) and (3, 0) are unique
    '''

    def check_only_true(indx, valid):
        possible_values = [0, 1, 2, "lots"]
        possible_values.remove(valid)
        assert filters.has_similar_shapes(indx, valid)
        for v in possible_values:
            assert not filters.has_similar_shapes(indx, v)

    # check uniques
    check_only_true((2, 1), 0)
    check_only_true((3, 0), 0)

    # check similar
    check_only_true((1, 0), 1)
    check_only_true((2, 0), 1)


def test_similar_shapes2():
    sample_grid = [
        [2, 1, 0, 1, 0],
        [1, 0, 1, 0, 1],
        [0, 1, 0, 1, 0],
        [1, 0, 1, 0, 1],
        [0, 1, 0, 1, 0],
        [1, 0, 1, 0, 1],
        [0, 1, 0, 1, 0],
        [1, 0, 1, 0, 1],
        [0, 1, 0, 2, 0],
        [3, 0, 0, 0, 0],
        [3, 3, 0, 0, 2]]

    ga, filters = create_ga(sample_grid)

    def check_only_true(indx, valid):
        possible_values = [0, 1, 2, "lots"]
        possible_values.remove(valid)
        assert filters.has_similar_shapes(indx, valid)
        for v in possible_values:
            assert not filters.has_similar_shapes(indx, v)

    # check uniques
    check_only_true((3, 0), 0)

    # check similar
    check_only_true((1, 0), "lots")
    check_only_true((1, 1), "lots")
    check_only_true((2, 0), "lots")


def get_rxe_task(name, show=False):
    tasks = loader.get_rxe_data()
    task = loader.filter_tasks(tasks, name)[0]
    if show:
        show_task(task)
    return task


def test_get_candidates():
    task = get_rxe_task("recolour_easy")

    # all in_grids
    graphs = [AbstractionFactory().create("scg_nb", sample.in_grid)
              for sample in (task.train_samples + task.test_samples)]

    bundle = GraphBundle(graphs)

    # testing PossibleValues...
    pb = PossibleValuesFilters(Filters.by_colour, bundle)
    all_args = list(pb.gen_all_possible())
    assert len(all_args) == 2

    # a bit brittle
    assert all_args == [('colour', [1, 'most', 'least']), ('exclude', [False, True])]
    all_combos = list(pb.product_of())
    assert len(all_combos) == 6
    assert {'colour': 1, 'exclude': False} in all_combos

    # testing get_candidate_filters()
    filter_instructions = filters.get_candidate_filters(bundle)
    assert len(filter_instructions) > 0

    # fish and search for best filter
    found = False
    for fis in filter_instructions:
        print(fis)
        if len(fis) == 1:
            fi = list(fis)[0]
            if fi.name == "by_size" and fi.params == {'size': 1, 'exclude': False}:
                found = True
                break

    assert found, "did not find the best filter"

    # no combos
    assert max(len(fis) for fis in filter_instructions) == 1


def test_get_candidates2():
    task = get_rxe_task("params_101")

    graphs = [AbstractionFactory().create("scg_nb", sample.in_grid)
              for sample in (task.train_samples + task.test_samples)]

    bundle = GraphBundle(graphs)
    filter_instructions = filters.get_candidate_filters(bundle, do_combined_filters=False)

    found_select_all = False
    found_by_size = False
    found_by_colour = False

    for fis in filter_instructions:
        assert len(fis) == 1
        fi = fis.list_of_fi[0]
        if fi.name == "select_all":
            found_select_all = True
        if fi.name == "by_size":
            found_by_size = True
        if fi.name == "by_colour":
            found_by_colour = True

    assert found_select_all
    assert found_by_size
    assert found_by_colour

    filter_instructions2 = filters.get_candidate_filters(bundle, do_combined_filters=True)

    assert len(filter_instructions2) > len(filter_instructions)
    found_multiple = False
    for fis in filter_instructions2:
        if len(fis) > 1:
            found_multiple = True
            print(fis)
    assert found_multiple
