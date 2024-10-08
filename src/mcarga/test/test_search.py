from competition import loader
from competition import runner

from mcarga import entry
from mcarga.search import mcts, mcts_scoring


def get_task(name, show=False):
    tasks = loader.get_kaggle_data(loader.WhichData.TRAIN)
    tasks += loader.get_kaggle_data(loader.WhichData.EVALUATION)
    tasks += loader.get_rxe_data()
    return loader.filter_tasks(tasks, name)[0]


def go(task, **kwds):
    show = kwds.pop("show", False)
    if show:
        runner.show_task(task)

    conf = mcts.Config()

    # default to 10 minutes
    conf.time_limit = kwds.pop("show", 60 * 10)

    # default to verbose logging
    conf.verbose_logging = kwds.pop("verbose_logging", False)

    for key, value in kwds.items():
        if hasattr(conf, key):
            setattr(conf, key, value)
        else:
            raise AttributeError(f"conf has no attribute '{key}'")

    print(conf)

    grids = [sample.in_grid for sample in task.train_samples]
    grids += [sample.in_grid for sample in task.test_samples]

    result = entry.go_ext(task, grids, conf=conf)

    if show:
        xr = runner.Result(task, show_test_answers=True)
        xr.train_predictions = result[:len(xr.train_predictions)]
        xr.test_predictions = result[len(xr.train_predictions):]
        xr.plot()


def test_recolour_easy():
    task = get_task("recolour_easy")
    go(task)


def test_recolour_easy__scoring_functions():
    task = get_task("recolour_easy")
    for sf in mcts_scoring.ScoringFunction:
        go(task, scoring_function=sf)


def test_recolour_two_objs():
    task = get_task("recolour_two_objs")
    go(task)


def test_recolour_two_objs__with_vcg():
    task = get_task("recolour_two_objs")
    go(task, time_limit=30, abstractions=["vcg_nb"])


def test_my_first_test():
    task = get_task("my_first_test")
    go(task)


def test_pixels_move():
    task = get_task("pixels_move_towards")
    go(task)


def test_pixels_move2():
    task = get_task("pixels_move_towards2")
    go(task)


def test_run_3():
    # tests moving towards another object
    task = get_task("05f2a901")
    go(task)


def test_run_4():
    task = get_task('42a50994')
    go(task)


def test_run_5():
    task = get_task('60b61512')
    go(task)


def test_run_6():
    task = get_task('a79310a0')
    go(task)


def test_run_7():
    task = get_task('ddf7fa4f')
    go(task)


def test_run_8():
    task = get_task('5ffb2104')
    go(task)


def test_run_9():
    task = get_task('4258a5f9')
    go(task)


def test_na():
    " na - - grid abstraction (dont think this works to be honest)  "
    for tid in "ed36ccf7 9dfd6313 6150a2bd 3c9b0459 74dd1130 67a3c6ac 68b16354 68b16354".split():
        task = get_task(tid)
        go(task)

if 0:
    # XXXX need to do this different, can be really slow and tests start to take much much longer when we change something unreleated.   We need a regression test suite to be run dailly.

    def test_eval_0():
        # this should be super easy, 2 instruction.  Took me a while to get the rule: any shape under
        # size 2 - colour green
        # XXX now takes 2 minutes
        task = get_task("12eac192")
        go(task, show=True, verbose_logging=True)


    def test_actually_easy2():
        # XXX actually fails... but should be easy
        task = get_train_task('543a7ed5')
        go(task, abstractions=["scg_nb_s2"])


    def test_actually_easy3():
        task = get_train_task('6455b5f5')
        go(task, abstractions=["scg"])


    def test_actually_easy4():
        task = get_train_task('23b5c85d')
        go(task, abstractions=["scg_nb_s2"])


    def test_problem_0():
        " erratic - sometimes passes, sometimes doesnt (it never legitmately passes - or scores 0)  "
        task = get_train_task("25d487eb")
        go(task)


    def test_problem_1():
        # real problem: '0d3d703e'
        for task_id in ('4258a5f9', '9565186b', 'd037b0a7'):
            task = get_train_task(task_id)
            go(task)


    def test_problem_2():
        ''' the tricky multi mapping that needs to be very deep across all examples '''
        task = get_train_task('0d3d703e')
        go(task)


    def test_hard_0():
        " passes fine, but it is five levels deep  "
        task = get_train_task("54d9e175")
        go(task)


    def test_hard_1():
        " hard cause the background is really not black  "
        task = get_train_task("543a7ed5")
        go(task)


    def test_wtf():
        " hard cause the background is really not black  "
        task = get_train_task("e9afcf9a")
        go(task)


    def test_long_0():
        task = get_rxe_task("test2")
        go(task)


    def test_should_pass():
        for task_id in "e8593010".split():
            task = get_train_task(task_id)
            go(task)


    def test_9edfc990():
        # program exists
        task = get_train_task("9edfc990")
        go(task, abstractions=["scg"])


    def test_810b9b61():
        # program exists
        task = get_train_task("810b9b61")
        go(task, abstractions=["scg_nb_s2"])


    def test_7f4411dc():
        # base case for lrg
        task = get_train_task("7f4411dc")
        go(task, abstractions=["lrg"])


    def test_91714a58():
        # lrg, harder variant of 7f4411dc (more noisy)
        task = get_train_task("91714a58")
        go(task, abstractions=["lrg"])


    def test_0d3d703e():
        task = get_train_task("0d3d703e")
        go(task)

