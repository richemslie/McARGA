import pdb
import sys
import pstats
import pprint
import cProfile
import traceback

from competition import runner

from mcarga.search.mcts import SearchEngine, Config

pprinter = pprint.PrettyPrinter(width=120).pprint


def go_ext(task, test_grids, **kwds):
    conf = kwds.get("conf", None)
    if conf is None:
        conf = Config(**kwds)

    conf.time_limit = 1000

    pprinter(conf)
    engine = SearchEngine(task, conf)

    print(f"mcarga: running - {task.task_id}")
    solving_time, reason = engine.solve()

    print(f"done {task.task_id} : {reason} in {solving_time:.1f} seconds")

    anode, instructions = engine.get_best_instructions()
    print()
    print(f"anode {anode.abstraction}")
    pprinter(instructions)
    print()
    pprinter(anode.stats)
    print()

    def tryx(grid):
        res = engine.apply_solution(grid, anode, instructions)
        if not res:
            res = runner.EMPTY
        return res

    return [tryx(g) for g in test_grids]


def go(task, test_grid, **kwds):
    return go_ext(task, [test_grid], **kwds)


class Profiler:
    def __init__(self, do_profiling=False, filename='profile.prof'):
        self.do_profiling = do_profiling
        self.filename = filename
        self.profiler = None

    def __enter__(self):
        if self.do_profiling:
            self.profiler = cProfile.Profile()
            self.profiler.enable()

        # Allows the with block to access the Profiler instance if needed (XXX probably not)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.do_profiling:
            self.profiler.disable()
            self.profiler.dump_stats(self.filename)

    def print_stats(self, n=10):
        if self.do_profiling:
            stats = pstats.Stats(self.filename)
            stats.strip_dirs()
            stats.sort_stats('cumulative')
            stats.print_stats(n)


def run(task, do_profiling=False, show_before_after=True, **kwds):
    if show_before_after:
        runner.show_task(task)

    grids = [sample.in_grid for sample in task.train_samples]
    grids += [sample.in_grid for sample in task.test_samples]

    result = None
    try:
        with Profiler(do_profiling=do_profiling):
            result = go_ext(task, grids, **kwds)

    except Exception as exc:
        print(exc)
        _, _, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)

    if show_before_after:
        xr = runner.Result(task, show_test_answers=True)
        xr.train_predictions = result[:len(xr.train_predictions)]
        xr.test_predictions = result[len(xr.train_predictions):]
        xr.plot()


def main():
    from competition import loader
    tasks = loader.get_kaggle_data(loader.WhichData.TRAIN, on_kaggle=False)

    for task_id in sys.argv[1:]:
        temp = loader.filter_tasks(tasks, task_id)
        task = temp[0]
        run(task, do_profiling=False, verbose_logging=True)


if __name__ == "__main__":
    main()
