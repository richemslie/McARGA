from mcarga.statemachine.scoring import arga_basic_scorer, arga_diff_grid_sizes, cmp_scorer
from .commontest import get_task_bundle


def do_arga_basic_scorer(in_ga, out_ga):
    reconstructed = in_ga.undo_abstraction()
    bg_colour = out_ga.background_colour
    return arga_basic_scorer(reconstructed, out_ga.original_grid, bg_colour)


def do_arga_diff_grid_sizes(in_ga, out_ga):
    reconstructed = in_ga.undo_abstraction()
    bg_colour = out_ga.background_colour
    return arga_diff_grid_sizes(reconstructed, out_ga.original_grid, bg_colour)


def do_cmp_scorer(in_ga, orig_ga, out_ga):
    reconstructed = in_ga.undo_abstraction()
    return cmp_scorer(reconstructed, orig_ga.original_grid, out_ga.original_grid)


def test_simple():
    for task_id in ["recolour_easy", "recolour_two_objs", "my_first_test", "6455b5f5"]:
        print(f"task_id: {task_id}")
        tb = get_task_bundle(task_id, show=False)

        for in_ga, out_ga in tb.pairs():
            score0 = do_arga_basic_scorer(in_ga, out_ga)
            score1 = do_arga_diff_grid_sizes(in_ga, out_ga)
            # since input and output shapes are the same
            assert score0 == score1
            print(score0)

        for in_ga, out_ga in tb.pairs():
            score = do_arga_basic_scorer(out_ga, out_ga)
            assert score == 0


def test_diff_sizes():
    # 7fe24cdd -> x4 larger
    # 88a62173 -> crop (x4 smaller)
    for task_id in ["7fe24cdd", "88a62173"]:
        print(f"task_id: {task_id}")
        tb = get_task_bundle(task_id, show=False)

        for in_ga, out_ga in tb.pairs():
            score1 = do_arga_diff_grid_sizes(in_ga, out_ga)
            print(score1)

        for in_ga, out_ga in tb.pairs():
            score = do_arga_diff_grid_sizes(out_ga, out_ga)
            assert score == 0


def test_cmp_scorer():
    for task_id in ["recolour_easy", "recolour_two_objs", "my_first_test", "6455b5f5", "7fe24cdd", "88a62173"]:
        print(f"task_id: {task_id}")
        tb = get_task_bundle(task_id, show=False)

        for in_ga, out_ga in tb.pairs():
            score = do_cmp_scorer(in_ga, in_ga, out_ga)
            print(score)

            score = do_cmp_scorer(out_ga, out_ga, out_ga)
            assert score == 0


def test_cmp_scorer_diff():
    for task_id in ["recolour_easy", "recolour_two_objs", "my_first_test", "7fe24cdd", "88a62173"]:
        tb = get_task_bundle(task_id, show=False)
        for in_ga, out_ga in tb.pairs():
            orig_ga = in_ga.copy()

            # modify colours of objects (underhand)
            for obj in in_ga.objs:
                # 9 is never input or output for any of the above tasks
                obj.colour = 9
                obj.update()
            in_ga.update_abstracted_graph()
            in_ga.fix_up_attrs()

            # now the score is worse for in_ga
            assert do_cmp_scorer(in_ga, orig_ga, out_ga) > do_cmp_scorer(orig_ga, orig_ga, out_ga)
