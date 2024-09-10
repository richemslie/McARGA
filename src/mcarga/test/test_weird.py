from competition import loader

from mcarga.selection import filters
from mcarga.abstractions.factory import AbstractionFactory

factory = AbstractionFactory()


def get_train_task(name):
    tasks = loader.get_kaggle_data(loader.WhichData.TRAIN)
    task = loader.filter_tasks(tasks, name)[0]
    return task


def test_no_abstraction_graph():
    def check(ga):
        # Check that the graph has only one node
        assert len(ga.objs) == 1
        assert ga.background_colour == 0

        # Get the single node
        ii = ga.indices()[0]
        oo = ga.get_obj(ii)

        # Check node properties
        assert oo.size > 16
        assert oo.colours == {1, 2, 3, 4, 7, 8}

        # Check that the abstraction type is correct
        assert ga.abstraction_type == "na"

    task = get_train_task("68b16354")

    for sample in task.train_samples:
        grid = sample.in_grid

        ga = factory.create("na", grid)
        check(ga)

    bundle_map = factory.create_all(task, ["na"])
    assert len(bundle_map) == 1
    task_bundle = bundle_map['na']
    for in_ga in task_bundle.in_train_bundle:
        check(in_ga)

    for in_ga in task_bundle.in_test_bundle:
        check(in_ga)

    for out_ga in task_bundle.out_bundle:
        check(out_ga)

    filters.get_candidate_filters(task_bundle.in_train_bundle)
