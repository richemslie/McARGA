import time


from pprint import pprint

from competition import loader

from mcarga.abstractions.factory import AbstractionFactory

from .commontest import get_blackboard_for_task_id


def test_blackboard():
    bb = get_blackboard_for_task_id("23b5c85d")


def test_analysisCC():
    ''' probably just delete this one '''
    bb = get_blackboard_for_task_id("0d3d703e")
    obj_match_mapping = bb.analysis()
    pprint(obj_match_mapping)


def do_anaysis(task_id, **kwds):
    bb = get_blackboard_for_task_id(task_id, **kwds)
    bb.analysis()

    print("mapping_in")
    pprint(bb.in_obj_match_mapping)
    print()

    print("mapping_out")
    pprint(bb.out_obj_match_mapping)
    print()

    return bb

def test_analysis_0():
    do_anaysis("0d3d703e")

    print("Exact:")
    for m in bb.get_exact_matches():
        print(m)

    print("static:")
    static = bb.get_static_object_for_insertion()
    print(static)
    X



def test_analysis_1():
    bb = do_anaysis("3bd67248", abstraction="scg_nb_dg")

    print("Exact:")
    for m in bb.get_exact_matches():
        print(m)

    print()
    print("Static:")
    static = bb.get_static_object_for_insertion()
    for m in static:
        print(m)


def test_bb_for_all():
    tasks = loader.get_kaggle_data(loader.WhichData.TRAIN_THESE)
    time_taken = {}
    bb_by_task = {}
    for task in tasks:
        # takes 20 seconds
        if task.task_id == "0dfd9992":
            continue

        s0 = time.time()
        bb = get_blackboard_for_task_id(task.task_id, show=False)
        mapping_in, mapping_out = bb.analysis_v2()

        print(f"task_id {task.task_id}")
        print("mapping_in")
        pprint(mapping_in)
        print()

        print("mapping_out")
        pprint(mapping_out)
        print()

        time_taken[task.task_id] = time.time() - s0

    pprint(sorted([(v, k) for k, v in time_taken.items()]))


    for task_id, lbb in lbb_by_task.items():
        filter_instructions = filters.get_candidate_filters(lbb.spe.task_bundle.in_train_bundle, do_combined_filters=False)

        mm = set(lbb.list_exact_matches())

        count = 0
        for f in filter_instructions:
            fi_objs = filters.gather_filtered_objects(f, lbb.spe.task_bundle.in_train_bundle)

            for fi_obj in fi_objs:
                if fi_obj in mm:
                    count += 1
                    break

        print(f"task_id {task_id} skips: {count} / {len(filter_instructions)}")
