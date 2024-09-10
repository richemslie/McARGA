import pytest

from competition import loader
from competition import runner

from mcarga.core.definitions import RelativeTo, Direction

from mcarga import parameters
from mcarga.instruction import FilterInstruction, FilterInstructions, TransformationInstruction, Instruction

from mcarga.abstractions.factory import AbstractionFactory


def get_task(name):

    tasks = loader.get_kaggle_data(loader.WhichData.TRAIN)
    tasks += loader.get_kaggle_data(loader.WhichData.EVALUATION)
    tasks += loader.get_rxe_data()

    task = loader.filter_tasks(tasks, name)[0]
    return task


def F(name, **params):
    fi = FilterInstruction(name, dict(params))
    return FilterInstructions(fi)


def FX(name, **params):
    return FilterInstruction(name, dict(params))


def Z(*fi):
    return FilterInstructions(*fi)


def T(name, **params):
    return TransformationInstruction(name, params)


class Program:
    def __init__(self, abstraction, *pairs):
        self.abstraction = abstraction
        self.instructions = [Instruction(fis, ti) for fis, ti in pairs]

    def apply_one(self, in_grid):
        factory = AbstractionFactory()
        ga = factory.create(self.abstraction, in_grid)

        # move state forward
        for instr in self.instructions:
            parameters.apply_instruction(ga, instr)

        reconstructed = ga.undo_abstraction()
        return reconstructed

    def check_task(self, task):
        for ss in task.train_samples:
            if self.apply_one(ss.in_grid) != ss.out_grid:
                return False

        for ss in task.test_samples:
            if self.apply_one(ss.in_grid) != ss.out_grid:
                return False

        return True

    def plot(self, task):
        xr = runner.Result(task, show_test_answers=True)

        xr.train_predictions = [self.apply_one(ss.in_grid) for ss in task.train_samples]
        xr.test_predictions = [self.apply_one(ss.in_grid) for ss in task.test_samples]
        xr.plot()

    def run(self, task):
        if not self.check_task(task):
            self.plot(task)
            assert False, "Fail to predict"


def test_apply_one():
    task = get_task("recolour_easy")

    # create a program
    p = Program("scg_nb",
                (F("select_all"), T("update_colour", colour=2)))

    for ss in task.train_samples:
        print("in_grid")
        print(ss.in_grid)

        predicted = p.apply_one(ss.in_grid)

        print("predicted")
        print(predicted)


def test_rxe__recolour_easy():
    task = get_task("recolour_easy")

    p = Program("scg_nb",
                (F("select_all"), T("update_colour", colour=2)))

    p.run(task)


def test_rxe__recolour_two_objs():
    task = get_task("recolour_two_objs")

    # 2 instructions
    p = Program("scg_nb",
                (F("by_colour", colour=3, exclude=False), T("update_colour", colour=4)),
                (F("by_colour", colour=1, exclude=False), T("update_colour", colour=2)))

    p.run(task)


def test_00d62c1b():
    " easy fill empty shape, requires scg_nb_s2 like abstraction "
    task = get_task("00d62c1b")
    p = Program("scg_nb_s2",
                (F("by_colour", colour=0, exclude=False), T("update_colour", colour=4)))
    p.run(task)


def test_08ed6ac7():
    " sorted by size "
    task = get_task("08ed6ac7")
    p = Program("scg_nb_s2",
                (F("by_size", size="max", exclude=False), T("update_colour", colour=1)),
                (F("by_size", size="2nd", exclude=False), T("update_colour", colour=2)),
                (F("by_size", size="3rd", exclude=False), T("update_colour", colour=3)),
                (F("by_size", size="min", exclude=False), T("update_colour", colour=4)))
    p.run(task)


def test_0d3d703e():
    " currently not solvable without swap colour (has been solved by fluke). "
    pytest.skip("requires some sort of swap")
    task = get_task("0d3d703e")
    p = Program("scg_nb_s2",
                (F("by_size", size="max", exclude=False), T("update_colour", colour=1)),
                (F("by_size", size="2nd", exclude=False), T("update_colour", colour=2)),
                (F("by_size", size="3rd", exclude=False), T("update_colour", colour=3)),
                (F("by_size", size="min", exclude=False), T("update_colour", colour=4)))
    p.run(task)


def test_1e0a9b12():
    # simple gravity task.  this has always solved by moving all objects down twice
    task = get_task("1e0a9b12")
    p = Program("scg_nb",
                (F("select_all"), T("move_object_max", direction=Direction.DOWN)),
                (F("select_all"), T("move_object_max", direction=Direction.DOWN)))
    p.run(task)


def test_25d487eb():
    # draw a line based on orientation of objects.  Has passed, but was fluke.
    pytest.skip("draw a line based on orientation of objects")
    task = get_task("25d487eb")
    p = Program("scg_nb_s2",
                (F("select_all"), T("move_object_max", direction=Direction.DOWN)),
                (F("select_all"), T("move_object_max", direction=Direction.DOWN)))
    p.run(task)


def test_25d8a9c8():
    # colour horizontal line - gray, rest black.  Has passed, but was fluke (and partial).
    pytest.skip("need to select horizontal lines")
    task = get_task("25d8a9c8")
    # partial solution
    p = Program("scg_nb",
                (F("by_size", size=3, exclude=False), T("update_colour", colour=5)),
                (F("by_size", size=3, exclude=True), T("update_colour", colour=0)))
    p.run(task)


def test_25ff71a9():
    " easy - move object down one "
    task = get_task("25ff71a9")

    # this fails to pick up the diagonal
    p = Program("scg_nb",
                (F("select_all"), T("move_object", direction=Direction.DOWN)))
    p.run(task)


def test_31aa019c():
    " tricky, but easily solved.  remove everything but the single pixel.  draw border around the said pixel. "
    task = get_task("31aa019c")

    # this fails to pick up the diagonal
    p = Program("scg_nb",
                (F("by_colour", colour="least", exclude=True), T("remove_object")),
                (F("select_all"), T("add_border_around_object", border_colour=2)))

    p.run(task)


def test_3618c87e():
    pytest.skip("overlap needs preference")
    task = get_task("3618c87e")

    p = Program("scg_nb",
                (F("by_colour", colour=1, exclude=False), T("move_object", direction=Direction.DOWN)))

    p.run(task)


def test_3aa6fb7a():
    " easy fill rectangle "
    task = get_task("3aa6fb7a")

    # this fails to pick up the diagonal
    p = Program("scg_nb",
                (F("select_all"), T("fill_rectangle", fill_colour=1, overlap=True)))
    p.run(task)


def test_60b61512():
    ''' fill rectangle, but need right abstraction '''

    task = get_task("60b61512")

    # this fails to pick up the diagonal
    p = Program("scg_nb",
                (F("select_all"), T("fill_rectangle", fill_colour=7, overlap=True)))

    assert not p.check_task(task)

    # changing the abstraction, this succeeds
    p = Program("scg_nb_dg",
                (F("select_all"), T("fill_rectangle", fill_colour=7, overlap=True)))

    p.run(task)


def test_6455b5f5():
    task = get_task("6455b5f5")

    # using scg - we can filter the empty grid spaces
    # XXX we should look into another way of getting grid spaces
    p = Program("scg",
                (F("by_size", size="max", exclude=False), T("update_colour", colour=1)),
                (F("by_size", size="min", exclude=False), T("update_colour", colour=8)))

    p.run(task)


def test_a48eeaf7():
    # harder gravity version (see also ae3edfdc)
    pytest.skip("need to add dnyamic params, or wait for new architecture")
    task = get_task("a48eeaf7")
    p = Program("scg",
                (F("by_size", size="max", exclude=False), T("update_colour", colour=1)))
    p.run(task)


def test_bb43febb():
    # simple hollow
    task = get_task("bb43febb")

    p = Program("scg_nb",
                (F("select_all"), T("hollow_rectangle", fill_colour=2)))
    p.run(task)


def test_ddf7fa4f():
    # base case of using dynamic params
    pass


def test_543a7ed5():
    # this should be fairly easy, but search couldnt find it
    # basically a draw green border and update colour
    task = get_task("543a7ed5")

    p = Program("scg_nb_s2",
                (F("by_colour", colour=6, exclude=False), T("add_border_around_object", border_colour=3)),
                (F("by_colour", colour=8, exclude=False), T("update_colour", colour=4)))
    p.run(task)


def test_56dc2b01():
    # another gravity case (move a to b), but then add a horizontal bar on top out of no where (insert?)
    pass


def test_623ea044():
    # finally a line drawing
    task = get_task("623ea044")

    p = Program("scg_nb",
                (F("by_size", size=1, exclude=False), T("draw_line", start_position=RelativeTo.TOP_LEFT,
                                                        direction=Direction.UP_LEFT, line_colour="self")),
                (F("by_size", size=1, exclude=False), T("draw_line", start_position=RelativeTo.TOP_RIGHT,
                                                        direction=Direction.UP_RIGHT, line_colour="self")),
                (F("by_size", size=1, exclude=False), T("draw_line", start_position=RelativeTo.BOTTOM_LEFT,
                                                        direction=Direction.DOWN_LEFT, line_colour="self")),
                (F("by_size", size=1, exclude=False), T("draw_line", start_position=RelativeTo.BOTTOM_RIGHT,
                                                        direction=Direction.DOWN_RIGHT, line_colour="self")))
    p.run(task)


def test_5c0a986e():
    # ok finally a draw_line that works!

    task = get_task("5c0a986e")
    p = Program("scg_nb",
                (F("by_colour", colour=1, exclude=False), T("draw_line", start_position=RelativeTo.TOP_LEFT,
                                                            direction=Direction.UP_LEFT, line_colour=1)),
                (F("by_colour", colour=2, exclude=False), T("draw_line", start_position=RelativeTo.BOTTOM_RIGHT,
                                                            direction=Direction.DOWN_RIGHT, line_colour=2)))
    p.run(task)


def test_7b6016b9():
    # this is a HUGE hack!
    task = get_task("7b6016b9")
    p = Program("scg_nb_s2",
                (F("by_colour", colour=0, exclude=False), T("update_colour", colour=2)),
                (F("by_colour", colour=2, exclude=False), T("change_background_colour", colour=3)))
    p.run(task)


def test_b230c067():
    task = get_task("b230c067")
    p = Program("scg_nb_dg",
                (F("by_size", size="min", exclude=False), T("update_colour", colour=2)),
                (F("by_size", size="max", exclude=False), T("update_colour", colour=1)))
    p.run(task)


def test_e73095fd():
    # fill partial background ...  very hard, has to only fill that are rectangle and fit the schema/shape
    pytest.skip("too hard, difference between non-background and background is like agi level! ;)")
    task = get_task("e73095fd")
    p = Program("scg_nb_s1",
                (F("by_colour", colour=0, exclude=False), T("update_colour", colour=4)))
    p.run(task)


def test_e8593010():
    # super easy!  map 3 different size to different colours.  but has gray background, and those shapes are all black
    # XXX yup only passes with 'scg_nb_s1' - which makes it not super easy.
    task = get_task("e8593010")
    p = Program("scg_nb_s1",
                (F("by_size", size=1, exclude=False), T("update_colour", colour=3)),
                (F("by_size", size=2, exclude=False), T("update_colour", colour=2)),
                (F("by_size", size=3, exclude=False), T("update_colour", colour=1)))
    p.run(task)


def test_3bd67248():
    # this is what I wanted to do all day (and wrote this whole test suite in the meantime)
    # it isnt it the 160
    # AND not sure it is going to work :(
    task = get_task("3bd67248")

    # LMAO ! It works!!  No way search will get it though. :(
    p = Program("scg_nb",
                # first hack, we move it up so that bottom and bottom_right are correct starting points
                (F("select_all"), T("move_object", direction=Direction.UP)),
                (F("select_all"), T("draw_line", start_position=RelativeTo.BOTTOM_RIGHT,
                                    direction=Direction.RIGHT, line_colour=4)),
                # miracle we can still access this via max
                (F("by_size", size="max", exclude=False), T("draw_line", start_position=RelativeTo.BOTTOM,
                                                            direction=Direction.UP_RIGHT, line_colour=2)),

                # and then we cant get it via max, and need AND filter!
                # oh yeah moving it back down, luckily it owns the overlap!
                (Z(FX("by_colour", colour=2, exclude=True),
                   FX("by_colour", colour=4, exclude=True)), T("move_object", direction=Direction.DOWN)))

    p.run(task)


def test_9edfc990():
    # flood fill, but can I do it with neighbours?  Sure can!
    task = get_task("9edfc990")
    p = Program("scg",
                (Z(FX("by_neighbour_colour", colour=1),
                   FX("by_colour", colour=0, exclude=False))
                 , T("update_colour", colour=1)))
    p.plot(task)


def test_810b9b61():
    # recolouring objects that have a have a neighbour - should work
    task = get_task("810b9b61")
    p = Program("scg_nb_s2",
                (F("by_neighbour_colour", colour=0),
                 T("update_colour", colour=3)))
    p.plot(task)
