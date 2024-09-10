from pprint import pprint

from common.grid import Grid

from mcarga.core import utils
from mcarga.core.definitions import Direction, Rotation, Mirror, SplitDirection, RelativeTo

from mcarga.abstractions.factory import AbstractionFactory

from mcarga.transformations.transformations import Transformations


factory = AbstractionFactory()


def test_transform_colour():
    sample_grid = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]]

    ga = factory.create("scg_nb", sample_grid)

    indices = ga.indices()
    assert len(indices) == 1
    index = indices[0]

    stored = utils.StoreAttributes.from_obj(ga.get_obj(index))

    t = Transformations(ga)
    t.update_colour(index, 3)

    stored.assert_all(ga.get_obj(index), "colour colours most_common_colour sig_str")

    ga.update_abstracted_graph()

    stored.assert_all(ga.get_obj(index), "colour colours most_common_colour sig_str")

    grid = ga.undo_abstraction()
    print(grid)


def test_transform_move():
    sample_grid = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]]

    ga = factory.create("scg_nb", sample_grid)

    def move(d):
        indices = ga.indices()
        assert len(indices) == 1
        index = indices[0]

        stored = utils.StoreAttributes.from_obj(ga.get_obj(index))

        t = Transformations(ga)
        t.move_object(index, d)

        stored.assert_all(ga.get_obj(index), "bound_box sig_str")

        ga.update_abstracted_graph()

        stored.assert_all(ga.get_obj(index), "bound_box sig_str")

        return ga.undo_abstraction()

    print()
    print(move(Direction.RIGHT))
    print()
    print(move(Direction.LEFT))
    print()
    print(move(Direction.DOWN_RIGHT))
    print()
    print(move(Direction.UP))
    print()
    print(move(Direction.UP_LEFT))
    print()
    print(move(Direction.DOWN))
    print()


def test_move_two_objects():
    sample_grid = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 2, 0],
        [0, 1, 1, 2, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]]

    def move(d, overlap):
        ga = factory.create("scg_nb", sample_grid)

        indices = ga.indices()
        assert len(indices) == 2

        index = indices[0]
        assert index[0] == 1
        obj = ga.get_obj(index)

        other = ga.get_obj(indices[1])
        assert obj.degree == 1
        assert other.degree == 1
        assert obj.edges[0] == (other, "horizontal")
        assert other.edges[0] == (obj, "horizontal")

        stored = utils.StoreAttributes.from_obj(obj)

        t = Transformations(ga)
        t.move_object(index, d)

        stored.assert_all(obj, "bound_box sig_str")

        ga.update_abstracted_graph()

        stored.assert_all(obj, "bound_box sig_str")

        assert obj == ga.get_obj(index)
        assert other == ga.get_obj(indices[1])

        assert obj.degree == 1
        assert other.degree == 1

        if overlap:
            assert obj.edges[0] == (other, "overlap")
            assert other.edges[0] == (obj, "overlap")
        else:
            assert obj.edges[0] == (other, "horizontal")
            assert other.edges[0] == (obj, "horizontal")

        return ga.undo_abstraction()

    print()
    print(move(Direction.LEFT, overlap=False))

    print()
    print(move(Direction.DOWN, overlap=False))

    print()
    print(move(Direction.UP, overlap=False))

    # oh, oh overlap!
    print()
    print(move(Direction.RIGHT, overlap=True))


def test_transform_extend():
    sample_grid = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]]

    def extend(d):
        ga = factory.create("scg_nb", sample_grid)

        print(f"Before:\n{ga.original_grid}")

        indices = ga.indices()
        assert len(indices) == 1
        index = indices[0]

        stored = utils.StoreAttributes.from_obj(ga.get_obj(index))

        t = Transformations(ga)
        t.extend_object(index, d)

        pprint(stored.diff(ga.get_obj(index)))
        stored.assert_all(ga.get_obj(index), "sig_shape bound_box size sig_str")

        ga.update_abstracted_graph()

        stored.assert_all(ga.get_obj(index), "sig_shape bound_box size sig_str")
        return ga.undo_abstraction()

    print()
    print(extend(Direction.LEFT))

    print()
    print(extend(Direction.RIGHT))


def test_move_object_max():
    sample_grid = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0]]

    def move(d):
        ga = factory.create("scg_nb", sample_grid)
        indices = ga.indices()
        assert len(indices) == 1
        index = indices[0]

        stored = utils.StoreAttributes.from_obj(ga.get_obj(index))

        t = Transformations(ga)
        t.move_object_max(index, d)

        stored.assert_all(ga.get_obj(index), "bound_box sig_str")

        ga.update_abstracted_graph()

        stored.assert_all(ga.get_obj(index), "bound_box sig_str")
        res = ga.undo_abstraction()

        print()
        print(d)
        print(res)

    move(Direction.RIGHT)
    move(Direction.UP_RIGHT)
    move(Direction.DOWN_RIGHT)
    move(Direction.LEFT)
    move(Direction.UP_LEFT)
    move(Direction.DOWN_LEFT)

    move(Direction.UP)
    move(Direction.DOWN)


def test_move_object_max_with_no_collisions():
    expanded_grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0],
        [0, 0, 0, 3, 3, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

    def move(d):
        ga = factory.create("scg_nb", expanded_grid)
        index = (1, 0)
        assert (1, 0) in ga.indices()

        stored = utils.StoreAttributes.from_obj(ga.get_obj(index))

        t = Transformations(ga)
        t.move_object_max((1, 0), d)

        stored.assert_all(ga.get_obj(index), "bound_box sig_str")

        ga.update_abstracted_graph()

        stored.assert_all(ga.get_obj(index), "bound_box sig_str")
        res = ga.undo_abstraction()

        print()
        print(d)
        print(res)

    move(Direction.RIGHT)
    move(Direction.UP_RIGHT)
    move(Direction.DOWN_RIGHT)
    move(Direction.LEFT)
    move(Direction.UP_LEFT)
    move(Direction.DOWN_LEFT)

    move(Direction.UP)
    move(Direction.DOWN)


def test_move_object_max_with_collisions():
    # XXX these tests need to check we collided or something
    expanded_grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 7, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 7, 7, 0, 0, 0, 0, 0, 2, 2, 2, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 8, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 9],
        [0, 8, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 9, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 4, 0, 0, 4, 4, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 5, 5, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

    def move(d):
        ga = factory.create("scg_nb", expanded_grid)
        index = 1, 0
        assert index in ga.indices()
        obj = ga.get_obj(index)

        stored = utils.StoreAttributes.from_obj(obj)

        t = Transformations(ga)
        t.move_object_max((1, 0), d)

        stored.assert_all(ga.get_obj(index), "bound_box sig_str")

        ga.update_abstracted_graph()
        res = ga.undo_abstraction()

        stored.assert_all(ga.get_obj(index), "bound_box sig_str")

        print()
        print(d)
        print(res)

    move(Direction.RIGHT)
    move(Direction.UP_RIGHT)
    move(Direction.DOWN_RIGHT)
    move(Direction.LEFT)
    move(Direction.UP_LEFT)
    move(Direction.DOWN_LEFT)

    move(Direction.UP)
    move(Direction.DOWN)


def test_rotations():

    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    def rotate(d):
        ga = factory.create("scg_nb", grid)
        index = 1, 0
        assert index in ga.indices()
        obj = ga.get_obj(index)

        stored = utils.StoreAttributes.from_obj(obj)

        t = Transformations(ga)
        t.rotate_object(index, d)

        stored.assert_all(ga.get_obj(index), ignore="sig_shape bound_box sig_str")

        ga.update_abstracted_graph()

        stored.assert_all(ga.get_obj(index), ignore="sig_shape bound_box sig_str")
        res = ga.undo_abstraction()

        print("START:")
        print(ga.original_grid)
        print()
        print(d)
        print(res)

    rotate(Rotation.CW)
    rotate(Rotation.CCW)
    rotate(Rotation.CW2)


def test_rotations_multi():

    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 2, 0, 0, 0],
            [0, 3, 3, 2, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    def rotate(d):
        ga = factory.create("mcg_nb", grid)
        # sz, 0
        index = 9, 0
        assert index in ga.indices()
        obj = ga.get_obj(index)

        stored = utils.StoreAttributes.from_obj(obj)

        t = Transformations(ga)
        t.rotate_object(index, d)

        stored.assert_all(ga.get_obj(index), ignore="sig_shape bound_box sig_str")

        ga.update_abstracted_graph()

        stored.assert_all(ga.get_obj(index), ignore="sig_shape bound_box sig_str")
        res = ga.undo_abstraction()

        print("START:")
        print(ga.original_grid)
        print()
        print(d)
        print(res)

    rotate(Rotation.CW)
    rotate(Rotation.CCW)
    rotate(Rotation.CW2)


def test_flip():
    grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0]
    ]

    def mirror_test(direction):
        ga = factory.create("scg_nb", grid)
        index = 1, 0
        assert index in ga.indices()
        obj = ga.get_obj(index)

        stored = utils.StoreAttributes.from_obj(obj)
        t = Transformations(ga)
        t.mirror_object(index, direction)

        stored.assert_all(ga.get_obj(index), ignore="sig_shape bound_box sig_str")
        ga.update_abstracted_graph()
        stored.assert_all(ga.get_obj(index), ignore="sig_shape bound_box sig_str")
        res = ga.undo_abstraction()

        print("START:")
        print(ga.original_grid)
        print()
        print(f"mirror direction: {direction}")
        print(res)

    mirror_test(Mirror.VERTICAL)
    mirror_test(Mirror.HORIZONTAL)
    mirror_test(Mirror.DIAGONAL_LEFT)
    mirror_test(Mirror.DIAGONAL_RIGHT)


def test_flip_multi():
    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 2, 0, 0, 0],
            [0, 3, 3, 2, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    def mirror_test(direction):
        ga = factory.create("mcg_nb", grid)
        index = 9, 0
        assert index in ga.indices()
        obj = ga.get_obj(index)

        stored = utils.StoreAttributes.from_obj(obj)
        t = Transformations(ga)
        t.mirror_object(index, direction)

        stored.assert_all(ga.get_obj(index), ignore="sig_shape bound_box sig_str")
        ga.update_abstracted_graph()
        stored.assert_all(ga.get_obj(index), ignore="sig_shape bound_box sig_str")
        res = ga.undo_abstraction()

        print("START:")
        print(ga.original_grid)
        print()
        print(f"mirror direction: {direction}")
        print(res)

    mirror_test(Mirror.VERTICAL)
    mirror_test(Mirror.HORIZONTAL)
    mirror_test(Mirror.DIAGONAL_LEFT)
    mirror_test(Mirror.DIAGONAL_RIGHT)


def test_reflect_axis():
    grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0]
    ]

    def reflect_axis_test(axis):
        ga = factory.create("scg_nb", grid)
        index = 1, 0
        assert index in ga.indices()

        t = Transformations(ga)

        t.reflect_axis(index, axis)

        ga.update_abstracted_graph()
        res = ga.undo_abstraction()
        print("START:")
        print(ga.original_grid)
        print()
        print(f"Mirror axis: {axis}")
        print(res)

    # Vertical mirror at j=3
    reflect_axis_test((None, 3))

    # Horizontal mirror at i=2
    reflect_axis_test((2, None))


def test_reflect_axis_long_grid():
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ]

    def reflect_axis_test(axis):
        ga = factory.create("scg_nb", grid)
        index = 1, 0
        assert index in ga.indices()

        t = Transformations(ga)

        t.reflect_axis(index, axis)

        ga.update_abstracted_graph()
        res = ga.undo_abstraction()
        print("START:")
        print(ga.original_grid)
        print()
        print(f"Mirror axis: {axis}")
        print(res)

    # Vertical mirror at j=3
    reflect_axis_test((None, 3))

    # Horizontal mirror at i=2
    reflect_axis_test((2, None))

    # Vertical mirror at j=6
    reflect_axis_test((None, 6))

    # This will be out of bounds
    reflect_axis_test((None, 0))


def test_reflect_axis_twice_long_grid():
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ]

    def reflect_axis_test(axis):
        ga = factory.create("scg_nb", grid)
        index = 1, 0
        assert index in ga.indices()
        obj = ga.get_obj(index)

        stored = utils.StoreAttributes.from_obj(obj)
        t = Transformations(ga)

        t.reflect_axis(index, axis)

        ga.update_abstracted_graph()
        res = ga.undo_abstraction()
        print("START:")
        print(ga.original_grid)
        print()
        print(f"Mirror axis: {axis}")
        print(res)

        t.reflect_axis(index, axis)
        stored.assert_all(ga.get_obj(index))
        ga.update_abstracted_graph()
        stored.assert_all(ga.get_obj(index))
        res = ga.undo_abstraction()

        print()
        print("Back again")
        print(res)

    # Vertical mirror at j=3
    reflect_axis_test((None, 3))

    # Horizontal mirror at i=2
    reflect_axis_test((2, None))

    # Vertical mirror at j=6
    reflect_axis_test((None, 6))

    # This will be out of bounds (it will go off screen)
    reflect_axis_test((None, 0))

    # This intercept the object (the object will just reflect itself)
    reflect_axis_test((None, 2))


def test_reflect_axis_assymmetric_weird():
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ]

    def reflect_axis_test(axis):
        ga = factory.create("scg_nb", grid)
        index = 1, 0
        assert index in ga.indices()
        obj = ga.get_obj(index)

        stored = utils.StoreAttributes.from_obj(obj)
        t = Transformations(ga)

        t.reflect_axis(index, axis)

        ga.update_abstracted_graph()
        res = ga.undo_abstraction()
        print("START:")
        print(ga.original_grid)
        print()
        print(f"Mirror axis: {axis}")
        print(res)

        t.reflect_axis(index, axis)
        stored.assert_all(ga.get_obj(index))
        ga.update_abstracted_graph()
        stored.assert_all(ga.get_obj(index))
        res = ga.undo_abstraction()

        print()
        print("Back again")
        print(res)

    # We reflect at various axes where the object exists
    reflect_axis_test((None, 0))
    reflect_axis_test((None, 1))
    reflect_axis_test((None, 2))
    reflect_axis_test((None, 4))
    reflect_axis_test((None, 4))


def test_reflect_axis_multiple_objs():
    ''' objects are reflected individually.  i wonder if we ever want to combine objects '''
    grid = [
        [0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 3, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 2, 2, 1, 3, 3, 0, 0, 0, 0, 0, 0],
        [0, 1, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ]

    def reflect_axis_test(axis):
        ga = factory.create("scg_nb", grid)
        for index in sorted(ga.indices()):
            obj = ga.get_obj(index)

            stored = utils.StoreAttributes.from_obj(obj)
            t = Transformations(ga)

            t.reflect_axis(index, axis)

            ga.update_abstracted_graph()
            res = ga.undo_abstraction()
            print("START:")
            print(ga.original_grid)
            print()
            print(f"Mirror axis: {axis}")
            print(res)

            t.reflect_axis(index, axis)
            stored.assert_all(ga.get_obj(index))
            ga.update_abstracted_graph()
            stored.assert_all(ga.get_obj(index))
            res = ga.undo_abstraction()

            print()
            print("Back again")
            print(res)

    # We reflect at various axes where the object exists
    reflect_axis_test((None, 6))


def test_add_border_around_object1():
    # solid shape
    simple_grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0]
    ]

    ga = factory.create("scg_nb", simple_grid)

    transformations = Transformations(ga)

    # Assuming the object we want to add a border to has index (1, 1)
    object_index = (1, 0)
    border_colour = 2

    # Call the function
    transformations.add_border_around_object(object_index, border_colour)

    # Check if the border was added correctly
    expected_result = Grid([
        [2, 2, 2, 2, 2],
        [2, 1, 1, 1, 2],
        [2, 1, 1, 1, 2],
        [2, 1, 1, 1, 2],
        [2, 2, 2, 2, 2]
    ])

    result = ga.undo_abstraction()
    assert result == expected_result


def test_add_border_around_object2():
    # hollow shape, notice it fills inside
    simple_grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ]

    ga = factory.create("scg_nb", simple_grid)
    print(ga.original_grid)

    transformations = Transformations(ga)

    # Assuming the object we want to add a border to has index (1, 1)
    object_index = (1, 0)
    border_colour = 5

    # Call the function
    transformations.add_border_around_object(object_index, border_colour)

    # Check if the border was added correctly (XXX I dont think we want this...
    expected_result = Grid([
        [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        [5, 1, 1, 1, 1, 1, 1, 1, 1, 5],
        [5, 1, 5, 5, 5, 5, 5, 5, 1, 5],
        [5, 1, 5, 0, 0, 0, 0, 5, 1, 5],
        [5, 1, 5, 5, 5, 5, 5, 5, 1, 5],
        [5, 1, 1, 1, 1, 1, 1, 1, 1, 5],
        [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
    ])

    result = ga.undo_abstraction()
    assert result == expected_result


def test_add_border_around_object_with_existing_objects():
    grid = [
        [0, 0, 3, 0, 0],
        [0, 1, 1, 1, 0],
        [3, 1, 1, 1, 3],
        [0, 1, 1, 1, 0],
        [0, 0, 3, 0, 0]
    ]

    ga = factory.create("scg_nb", grid)
    transformations = Transformations(ga)

    object_index = (1, 0)
    border_colour = 2

    transformations.add_border_around_object(object_index, border_colour)

    expected_result = Grid([
        [2, 2, 3, 2, 2],
        [2, 1, 1, 1, 2],
        [3, 1, 1, 1, 3],
        [2, 1, 1, 1, 2],
        [2, 2, 3, 2, 2]
    ])

    result = ga.undo_abstraction()
    assert result == expected_result


def test_transform_over_and_over():
    grid = Grid([
        [0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 3, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 2, 2, 1, 3, 3, 0, 0, 0, 0, 0, 0],
        [0, 1, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ])

    orig_ga = factory.create("scg_nb", grid)

    for ii in range(100):
        ga = orig_ga.copy()
        for index in ga.indices():
            new_ga = ga.copy()
            assert new_ga.indices() == orig_ga.indices()

            gg1 = ga.undo_abstraction()
            gg2 = new_ga.undo_abstraction()
            assert gg1 == gg2

            t = Transformations(ga)
            t.update_colour(index, 5)
            ga.update_abstracted_graph()

            t = Transformations(new_ga)
            t.update_colour(index, 5)
            new_ga.update_abstracted_graph()

            gg1 = ga.undo_abstraction()
            gg2 = new_ga.undo_abstraction()
            assert gg1 == gg2

        assert ga.indices() == new_ga.indices()
        assert len(ga.indices()) == 3

        # the original is not touched
        assert orig_ga.undo_abstraction() == grid


def test_transform_remove():
    sample_grid = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]]

    ga = factory.create("scg_nb", sample_grid)

    indices = ga.indices()
    assert len(indices) == 1
    index = indices[0]

    t = Transformations(ga)
    t.remove_object(index)

    grid = ga.undo_abstraction()
    print(grid)


def test_splitting():

    grid0 = [[0, 0, 0, 0, 0, 0, 0],
             [0, 0, 1, 1, 1, 0, 0],
             [0, 0, 0, 1, 0, 0, 0],
             [0, 0, 0, 1, 0, 0, 0],
             [0, 0, 0, 1, 1, 0, 0],
             [0, 0, 0, 0, 0, 0, 0]]

    grid1 = [[0, 0, 0, 0, 0, 0, 0],
             [0, 1, 1, 1, 1, 0, 0],
             [0, 1, 0, 0, 1, 0, 0],
             [0, 1, 0, 0, 1, 0, 0],
             [0, 1, 1, 1, 1, 0, 0],
             [0, 0, 0, 0, 0, 0, 0]]

    grid2 = [[0, 0, 0, 0, 0, 0, 0],
             [0, 1, 1, 1, 1, 0, 0],
             [0, 1, 0, 0, 1, 0, 0],
             [0, 1, 0, 0, 1, 0, 0],
             [0, 1, 0, 0, 1, 0, 0],
             [0, 1, 0, 0, 1, 0, 0],
             [0, 1, 0, 0, 1, 0, 0],
             [0, 1, 0, 0, 1, 0, 0],
             [0, 1, 0, 0, 1, 0, 0],
             [0, 1, 0, 0, 1, 0, 0],
             [0, 1, 1, 1, 1, 0, 0],
             [0, 0, 0, 0, 0, 0, 0]]

    for grid in (grid0, grid1, grid2):
        for dd in SplitDirection.VERTICAL, SplitDirection.HORIZONTAL:
            ga = factory.create("scg_nb", grid)
            index = 1, 0
            assert index in ga.indices()

            assert len(ga.indices()) == 1

            t = Transformations(ga)
            t.split_object(index, dd)

            ga.update_abstracted_graph()

            assert len(ga.indices()) == 2

            # colour one red so can see difference
            t.update_colour(ga.indices()[1], 2)
            ga.update_abstracted_graph()

            print("Before:")
            print(ga.original_grid)

            print("After:")
            print(ga.undo_abstraction())


def test_fill_rectangle():

    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    ga = factory.create("scg_nb", grid)

    transformations = Transformations(ga)

    # Assuming the object we want to add a border to has index (1, 1)
    object_index = (1, 0)

    # Call the function
    transformations.fill_rectangle(object_index, 2, overlap=False)

    # Check if the border was added correctly
    expected_result = Grid([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 2, 1, 2, 0, 0],
        [0, 0, 2, 1, 2, 0, 0],
        [0, 0, 2, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0]])

    result = ga.undo_abstraction()
    assert result == expected_result


def test_fill_rectangle2():

    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 1, 1, 1, 0, 1, 0],
            [0, 0, 1, 1, 0, 1, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    ga = factory.create("scg_nb", grid)

    transformations = Transformations(ga)

    # Assuming the object we want to add a border to has index (1, 1)
    object_index = (1, 0)

    # Call the function
    transformations.fill_rectangle(object_index, 2, overlap=False)

    # Check if the border was added correctly
    expected_result = Grid([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 2, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 2, 1, 0],
        [0, 2, 1, 1, 2, 1, 0],
        [0, 2, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0]])

    result = ga.undo_abstraction()
    assert result == expected_result


def test_fill_rectangle3():

    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 0, 3, 1, 1, 1, 0],
            [0, 1, 3, 1, 0, 1, 0],
            [0, 0, 3, 1, 0, 1, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    ga = factory.create("mcg_nb", grid)

    transformations = Transformations(ga)

    # Assuming the object we want to add a border to has index (1, 1)
    object_index = (14, 0)
    assert object_index in ga.indices()

    # Call the function
    transformations.fill_rectangle(object_index, 7, overlap=False)

    # Check if the border was added correctly
    expected_result = Grid([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 7, 3, 1, 1, 1, 0],
        [0, 1, 3, 1, 7, 1, 0],
        [0, 7, 3, 1, 7, 1, 0],
        [0, 7, 1, 1, 1, 7, 0],
        [0, 0, 0, 0, 0, 0, 0]])

    result = ga.undo_abstraction()
    assert result == expected_result


def test_hollow_rectangle1():
    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    ga = factory.create("scg_nb", grid)

    transformations = Transformations(ga)

    # Assuming the object we want to add a border to has index
    object_index = (1, 0)
    assert object_index in ga.indices()

    # Call the function
    transformations.hollow_rectangle(object_index, 0)

    result = ga.undo_abstraction()
    expected_result = Grid([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0]])

    assert result == expected_result


def test_hollow_rectangle2():
    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 1, 1, 0, 0, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    ga = factory.create("scg_nb", grid)

    transformations = Transformations(ga)

    # Assuming the object we want to add a border to has index
    object_index = (1, 0)
    assert object_index in ga.indices()

    # Call the function
    transformations.hollow_rectangle(object_index, 0)

    result = ga.undo_abstraction()
    expected_result = Grid([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0]])

    assert result == expected_result


def test_hollow_rectangle3():
    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    ga = factory.create("scg_nb", grid)

    transformations = Transformations(ga)

    # Assuming the object we want to add a border to has index
    object_index = (1, 0)
    assert object_index in ga.indices()

    # Call the function
    transformations.hollow_rectangle(object_index, 0)

    result = ga.undo_abstraction()
    expected_result = Grid([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0]])

    assert result == expected_result


def test_hollow_rectangle4():
    grid = [[0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0]]

    ga = factory.create("scg_nb", grid)

    transformations = Transformations(ga)

    # Assuming the object we want to add a border to has index
    object_index = (1, 0)
    assert object_index in ga.indices()

    # Call the function
    transformations.hollow_rectangle(object_index, 0)

    result = ga.undo_abstraction()
    expected_result = Grid([
        [0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0]])

    assert result == expected_result


def test_draw_one():
    sample_grid = [
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0]]

    colour = 3

    def draw_one(p, d):
        ga = factory.create("scg_nb", sample_grid)

        print(f"Before:\n{ga.original_grid}")

        indices = ga.indices()
        assert len(indices) == 1
        index = indices[0]

        t = Transformations(ga)
        t.draw_line(index, p, d, colour)

        ga.update_abstracted_graph()

        return ga.undo_abstraction()

    print()
    print(draw_one(RelativeTo.BOTTOM_RIGHT, Direction.RIGHT))
    print(draw_one(RelativeTo.BOTTOM, Direction.DOWN_RIGHT))
    print(draw_one(RelativeTo.RIGHT, Direction.RIGHT))
    print(draw_one(RelativeTo.BOTTOM, Direction.UP_RIGHT))


def test_draw_another():
    sample_grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

    colour = 3

    def draw_one(p, d):
        print(f"draw_line(... {p}, {d}, ...)")
        print("================================================")
        ga = factory.create("scg_nb", sample_grid)

        print(f"Before:\n{ga.original_grid}")

        indices = ga.indices()
        assert len(indices) == 1
        index = indices[0]

        t = Transformations(ga)
        t.draw_line(index, p, d, colour)

        ga.update_abstracted_graph()

        return ga.undo_abstraction()

    print()
    print(draw_one(RelativeTo.RIGHT, Direction.RIGHT))
    print(draw_one(RelativeTo.LEFT, Direction.LEFT))
    print(draw_one(RelativeTo.TOP, Direction.UP))
    print(draw_one(RelativeTo.BOTTOM, Direction.DOWN))

    print()

    print(draw_one(RelativeTo.TOP_LEFT, Direction.UP_LEFT))
    print(draw_one(RelativeTo.TOP_RIGHT, Direction.UP_RIGHT))
    print(draw_one(RelativeTo.BOTTOM_LEFT, Direction.DOWN_LEFT))
    print(draw_one(RelativeTo.BOTTOM_RIGHT, Direction.DOWN_RIGHT))


def test_draw_another_2():
    sample_grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

    colour = 4

    def draw_one(p, d):
        print(f"draw_line(... {p}, {d}, ...)")
        print("================================================")
        ga = factory.create("scg_nb", sample_grid)

        print(f"Before:\n{ga.original_grid}")

        indices = ga.indices()
        assert len(indices) == 1
        index = indices[0]

        t = Transformations(ga)
        t.draw_line(index, p, d, colour)

        ga.update_abstracted_graph()

        return ga.undo_abstraction()

    print()
    print(draw_one(RelativeTo.RIGHT, Direction.RIGHT))
    print(draw_one(RelativeTo.LEFT, Direction.LEFT))
    print(draw_one(RelativeTo.TOP, Direction.UP))
    print(draw_one(RelativeTo.BOTTOM, Direction.DOWN))

    print()

    print(draw_one(RelativeTo.TOP_LEFT, Direction.UP_LEFT))
    print(draw_one(RelativeTo.TOP_RIGHT, Direction.UP_RIGHT))
    print(draw_one(RelativeTo.BOTTOM_LEFT, Direction.DOWN_LEFT))
    print(draw_one(RelativeTo.BOTTOM_RIGHT, Direction.DOWN_RIGHT))
