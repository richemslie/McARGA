from pprint import pprint

from competition import loader
from competition import runner

from mcarga.core.utils import Timer

from mcarga.abstractions.factory import AbstractionFactory

from mcarga.statemachine.blackboard import Blackboard

from mcarga.statemachine.rollout import perform_monte_carlo

from .commontest import get_rxe_task, get_train_task


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

    bb = Blackboard(bundle)

    mapping = bb.analysis()
    pprint(mapping)


def run(task_id, abstraction=None):
    if abstraction:
        bundle = get_task_bundle(task_id, abstraction)
    else:
        bundle = get_task_bundle(task_id)

    with Timer("Blackboard creation"):
        bb = Blackboard(bundle)
        bb.analysis()
        mapping = bb.in_obj_match_mapping

    for indx, pair in enumerate(bundle.pairs()):
        if perform_monte_carlo(mapping[indx], pair):
            print("SUCCESS")
        else:
            print("FAIL")


def test_simple_run0():
    run("recolour_easy")





def test_simple_run1():
    bundle = get_task_bundle("recolour_two_objs")

    bb = Blackboard(bundle)

    mapping = bb.analysis()

    for indx, pair in enumerate(bundle.pairs()):
        if perform_monte_carlo(mapping[indx], pair):
            print("SUCCESS")
        else:
            print("FAIL")


def test_simple_run2():
    bundle = get_task_bundle("my_first_test")

    bb = Blackboard(bundle)

    mapping = bb.analysis()

    for indx, pair in enumerate(bundle.pairs()):
        if perform_monte_carlo(mapping[indx], pair):
            print("SUCCESS")
        else:
            print("FAIL")


def test_simple_run3():
    bundle = get_task_bundle("test2")

    bb = Blackboard(bundle)

    mapping = bb.analysis()

    for indx, pair in enumerate(bundle.pairs()):
        if perform_monte_carlo(mapping[indx], pair):
            print("SUCCESS")
        else:
            print("FAIL")


def test_zzz():
    bundle = get_task_bundle("6455b5f5", "scg")

    with Timer("Blackboard creation"):
        bb = Blackboard(bundle)

    with Timer("bb.analysis"):
        mapping = bb.analysis()

    for indx, pair in enumerate(bundle.pairs()):

        with Timer("perform_monte_carlo"):
            if perform_monte_carlo(mapping[indx], pair):
                print("SUCCESS")
            else:
                print("FAIL")

