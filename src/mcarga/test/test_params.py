from competition import loader
from competition.runner import show_task

from mcarga.abstractions.factory import AbstractionFactory, GraphBundle

from mcarga.transformations import transformations as trans

from mcarga import parameters
from mcarga.instruction import FilterInstruction, FilterInstructions, TransformationInstruction, Instruction


def get_task(name, show=True):
    tasks = loader.get_rxe_data()
    task = loader.filter_tasks(tasks, name)[0]
    if show:
        show_task(task)
    return task


def get_bundle(task, abstraction):
    graphs = [AbstractionFactory().create(abstraction, sample.in_grid)
              for sample in (task.train_samples + task.test_samples)]

    return GraphBundle(graphs)


def simple_fi(name, **kwds):
    fi = FilterInstruction(name, dict(kwds))
    return FilterInstructions(fi)


def test_apply_instruction():
    task = get_task("recolour_easy", show=False)
    bundle = get_bundle(task, "scg_nb")
    fis = simple_fi("by_colour", colour=1, exclude=False)
    ti = TransformationInstruction("update_colour", dict(colour=2))
    ii = Instruction(fis, ti)

    for ga in bundle:
        parameters.apply_instruction(ga, ii)

        print("BEFORE")
        print(ga.original_grid)
        print("AFTER")
        print(ga.undo_abstraction())


def test_gen_params1():
    task = get_task("recolour_easy", show=False)
    bundle = get_bundle(task, "scg_nb")

    gen = trans.generate_params_for_transformation("rotate_object", bundle)

    instructions = list(gen)
    for i in instructions:
        assert not i.has_param_binding()
        print(i)

    # 3 directions
    assert len(instructions) == 3


def test_gen_params2():
    task = get_task("params_101", show=False)
    bundle = get_bundle(task, "scg_nb")

    gen = trans.generate_params_for_transformation("hollow_rectangle", bundle)

    instructions = list(gen)
    for i in instructions:
        assert not i.has_param_binding()
        print(i)

    # 10 colours
    assert len(instructions) == 10


def test_candidate_instructions():
    pytest.skip("XXX we need to refactor code out of search")
    task = get_task("recolour_easy", show=False)
    bundle = get_bundle(task, "scg_nb")

    fis = simple_fi("by_colour", colour=1, exclude=False)

    transformations = ["update_colour", "move_object"]

    dyn = parameters.generate_dynamic_params(fis, bundle)

    all_instructions = []
    for ti in trans.get_all_transformations(transformations, bundle):
        ii = Instruction(fis, ti)
        if ii.has_param_binding():
            ii.set_param_binding_instruction(dyn)

        all_instructions.append(ii)

    for input_ga in bundle:
        for ii in all_instructions:
            ga = input_ga.copy()
            parameters.apply_instruction(ga, ii)


def test_with_param_binding():
    pytest.skip("XXX we need to refactor code out of search")
    task = get_task("params_101", show=False)
    bundle = get_bundle(task, "scg_nb")

    fis = simple_fi("by_size", size="max", exclude=False)
    transformations = ["update_colour"]

    dyn = parameters.generate_dynamic_params(fis, bundle)

    all_instructions = []
    for ti in trans.get_all_transformations(transformations, bundle):
        ii = Instruction(fis, ti)
        if ii.has_param_binding():
            ii.set_param_binding_instruction(dyn)

        all_instructions.append(ii)

    for input_ga in bundle:
        for ii in all_instructions:
            ga = input_ga.copy()
            parameters.apply_instruction(ga, ii)

    # we know in this case that the dynamic param binding solves task, so we only
    # print those
    for input_ga in bundle:
        for ii in all_instructions:
            if not ii.has_param_binding():
                continue

            ga = input_ga.copy()
            parameters.apply_instruction(ga, ii)

            print("BEFORE")
            print(ga.original_grid)
            print("AFTER")
            print(ga.undo_abstraction())

