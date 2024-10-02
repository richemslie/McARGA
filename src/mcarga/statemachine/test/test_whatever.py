from pprint import pprint

from competition import loader
from competition import runner

from mcarga.core.utils import Timer

from mcarga.abstractions.factory import AbstractionFactory

from mcarga.statemachine.blackboard import Blackboard

from mcarga.statemachine.rollout import perform_monte_carlo


def get_rxe_task(name, show=True):
    tasks = loader.get_rxe_data()
    task = loader.filter_tasks(tasks, name)[0]
    runner.show_task(task)
    return task


def get_train_task(name, show=True):
    tasks = loader.get_kaggle_data(loader.WhichData.TRAIN)
    task = loader.filter_tasks(tasks, name)[0]
    runner.show_task(task)
    return task


def test_get_abstraction():
    task = get_rxe_task("recolour_easy")
    factory = AbstractionFactory()

    bundle_map = factory.create_all(task, ["scg_nb"])
    assert len(bundle_map) == 1
    task_bundle = bundle_map['scg_nb']

    for in_ga, out_ga in task_bundle.pairs():
        in_grid = in_ga.undo_abstraction()
        out_grid = out_ga.undo_abstraction()
        print("IN")
        print(in_grid)

        print("OUT")
        print(out_grid)


def get_task_bundle(task_id, abstraction="scg_nb"):
    try:
        task = get_rxe_task(task_id)
    except IndexError:
        task = get_train_task(task_id)

    factory = AbstractionFactory()

    bundle_map = factory.create_all(task, [abstraction])
    assert len(bundle_map) == 1
    task_bundle = bundle_map[abstraction]

    return task_bundle


def test_create_blackboard():
    bundle = get_task_bundle("recolour_easy")

    lbb = Blackboard(bundle)

    mapping = lbb.analysis()
    pprint(mapping)


def test_simple_run0():
    bundle = get_task_bundle("recolour_easy")

    lbb = Blackboard(bundle)

    mapping = lbb.analysis()

    for indx, pair in enumerate(bundle.pairs()):
        if perform_monte_carlo(mapping[indx], pair):
            print("SUCCESS")
        else:
            print("FAIL")


def test_simple_run1():
    bundle = get_task_bundle("recolour_two_objs")

    lbb = Blackboard(bundle)

    mapping = lbb.analysis()

    for indx, pair in enumerate(bundle.pairs()):
        if perform_monte_carlo(mapping[indx], pair):
            print("SUCCESS")
        else:
            print("FAIL")


def test_simple_run2():
    bundle = get_task_bundle("my_first_test")

    lbb = Blackboard(bundle)

    mapping = lbb.analysis()

    for indx, pair in enumerate(bundle.pairs()):
        if perform_monte_carlo(mapping[indx], pair):
            print("SUCCESS")
        else:
            print("FAIL")


def test_simple_run3():
    bundle = get_task_bundle("test2")

    lbb = Blackboard(bundle)

    mapping = lbb.analysis()

    for indx, pair in enumerate(bundle.pairs()):
        if perform_monte_carlo(mapping[indx], pair):
            print("SUCCESS")
        else:
            print("FAIL")


def test_hard_but_actually_easy():
    # first mcts search is #tis 92 / *instrs 3864
    # insane!  - DID timeout, and that is just one abstraction

    bundle = get_task_bundle("6455b5f5", "scg")

    with Timer("Blackboard creation"):
        lbb = Blackboard(bundle)

    with Timer("lbb.analysis"):
        mapping = lbb.analysis()

    for indx, pair in enumerate(bundle.pairs()):

        with Timer("perform_monte_carlo"):
            if perform_monte_carlo(mapping[indx], pair):
                print("SUCCESS")
            else:
                print("FAIL")

