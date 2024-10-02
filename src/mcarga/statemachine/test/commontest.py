from competition import loader
from competition import runner

from mcarga.abstractions.factory import AbstractionFactory
from mcarga.statemachine.blackboard import Blackboard


def get_rxe_task(name, show=False):
    tasks = loader.get_rxe_data()
    task = loader.filter_tasks(tasks, name)[0]
    if show:
        runner.show_task(task)
    return task


def get_train_task(name, show=False):
    tasks = loader.get_kaggle_data(loader.WhichData.TRAIN)
    task = loader.filter_tasks(tasks, name)[0]
    if show:
        runner.show_task(task)
    return task


def get_task_bundle(task_id, abstraction="scg_nb", show=False):
    try:
        task = get_rxe_task(task_id, show=show)
    except IndexError:
        task = get_train_task(task_id, show=show)

    factory = AbstractionFactory()

    bundle_map = factory.create_all(task, [abstraction])
    assert len(bundle_map) == 1
    task_bundle = bundle_map[abstraction]

    return task_bundle


def get_blackboard_for_task_id(task_id, abstraction="scg_nb", show=False):
    task_bundle = get_task_bundle(task_id, abstraction=abstraction, show=show)
    return Blackboard(task_bundle)

