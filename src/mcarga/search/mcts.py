import sys
import math
import time
import traceback
from typing import List
from collections import deque

from dataclasses import dataclass

from competition import loader

from mcarga.core.alogger import log, Logger
from mcarga.core.baseenum import BaseEnum, auto

from mcarga.transformations import config as tconfig

from mcarga.selection import filters
from mcarga.abstractions import factory
from mcarga import parameters
from mcarga.transformations import transformations as trans
from mcarga.instruction import Instruction
from mcarga.search.mcts_scoring import Scoring, ScoringFunction


@dataclass
class Stats:
    number_of_children: int = 0
    total_filter_instructions: int = 0
    total_instructions: int = 0
    total_children_added: int = 0
    errors_creating_child: int = 0


class SearchStatus(BaseEnum):
    ContinueRunning = auto()
    SolutionFound = auto()
    NoSolutionFound = auto()
    TimeoutInitialiseRoot = auto()


@dataclass
class Config:
    verbose_create_child: bool = False

    abstractions: List[str] = ("scg_nb", "scg_nb_dg", "scg_nb_s1", "scg_nb_s2", "mcg_nb", "scg","lrg", "vcg_nb", "na")

    expand_children_max: int = 500

    # this makes testing easier
    do_combined_filters: bool = False

    # maximum time limit for search, in seconds.
    time_limit: int = 60

    # whether to store the state in hashmap, so we have less nodes in search tree
    do_hashing: bool = True

    # when hashing includeing the signature of objects as well as the reconstructed grid
    hashing_include_objects_sigs: bool = True

    prune_worse_scores: bool = True
    prune_worse_keep_anyway: int = 8

    # these tune mcts exploration
    child_ucb_constant: float = 0.85
    child_initial_visits_constant: int = 4

    verbose_logging: bool = False

    scoring_function: ScoringFunction = ScoringFunction.PENALISE_DIFF_ORIG_COLOURS


class AbstractionNode:
    def __init__(self, task_bundle):
        self.abstraction = task_bundle.abstraction

        # original bundle
        self.task_bundle = task_bundle

        self.root_node = None
        self.seen_tokens = set()

        self.visits = 0
        self.stats = Stats()

    def check_seen_token(self, token):
        return token in self.seen_tokens

    def add_token_to_seen(self, token):
        self.seen_tokens.add(token)

    def orig_input_bundle(self):
        ' return a copy of input bundle '
        in_train_bundle = self.task_bundle.in_train_bundle.copy()
        in_test_bundle = self.task_bundle.in_test_bundle.copy()
        for g in in_train_bundle:
            g.is_training_graph = True

        for g in in_test_bundle:
            g.is_training_graph = False

        return in_train_bundle + in_test_bundle

    @property
    def best_score(self):
        return self.root_node.best_score


class SearchNodeChild:
    # these are set are start from config
    UCB_CONSTANT = None
    INITIAL_VISITS_CONSTANT = None

    def __init__(self, instruction, parent, score, token):
        self.instruction = instruction
        self.search_tree_node = parent
        self.score = score

        # ability to lookup later
        self.token = token

        # the next node
        self.next = None

        self.visits = self.INITIAL_VISITS_CONSTANT

    def incr_visits(self):
        self.visits += 1

    def normalise_score(self, node_score):
        return 1.0 - self.score / node_score

    def exploration_bonus(self, parent_visits):
        return self.UCB_CONSTANT * math.sqrt(math.log(parent_visits + 1) / (self.visits))

    def uct_score(self, node_score, parent_visits):
        return self.normalise_score(node_score) + self.exploration_bonus(parent_visits)


class SearchTreeNode:
    def __init__(self, back_link, original_score):
        # can be one of SearchNodeChild or AbstractionNode (the later terminating back prop)
        self.back_link = back_link
        self.original_score = original_score
        self.best_score = original_score

        self.children = []
        self.pruned = []
        self.visits = 1

        # set later - stats:
        self.total_filter_instructions = 0
        self.total_instructions = 0

        self.todo_instructions = deque()

    def finished_expanding(self):
        if len(self.todo_instructions) == 0:
            return True

        if self.best_score == 0:
            return True

        return False

    def incr_visits(self):
        self.visits += 1

    def update(self):
        if not self.children:
            return

        # this is rough for performance!
        self.children.sort(key=lambda x: x.score)

        # lowest score
        self.best_score = self.children[0].score

        self.children.sort(key=lambda x: x.uct_score(self.original_score, self.visits), reverse=True)

    def add(self, child):
        self.children.append(child)

    def dump(self, max_count, prefix="", only_better_than_orig=False):

        log(f"{prefix}Dumping node - with original score: {self.original_score} --> {self.best_score}")
        nfi, ni = self.total_filter_instructions, self.total_instructions
        log(f"{prefix}#filters: {nfi} #instruction: {ni}, #children: {len(self.children)} visits: {self.visits}")

        # sort by visits for dumping
        self.children.sort(key=lambda x: x.visits, reverse=True)

        for i, c in enumerate(self.children):
            if only_better_than_orig and c.score >= self.original_score:
                break

            ns = c.normalise_score(self.original_score)
            uct = c.uct_score(self.original_score, self.visits)
            log(f"{prefix}{i}: {c.score}/{(ns):.2f}/{c.visits}/{uct:.2f} {c.instruction}")

            if i > max_count:
                break

    def prune_worse(self, config):
        # ensure we are sorted first
        self.children.sort(key=lambda x: x.score)

        olen = len(self.children)
        keep = []
        pruned = []
        for i, c in enumerate(self.children + self.pruned):
            if i < config.prune_worse_keep_anyway:
                keep.append(c)
            elif c.score <= self.original_score:
                keep.append(c)
            else:
                pruned.append(c)

        self.children = keep
        self.pruned = pruned
        self.update()
        log(f"Pruned {olen - len(self.children)} children")

    def __repr__(self):
        num_child = len(self.children)
        orig_score = self.original_score
        best_score = self.best_score
        return f"STN - #children {num_child}, oscore/bscore/visits: {orig_score} / {best_score} / {self.visits}"


class SearchEngine:
    def __init__(self, task: loader.Task, config: Config):

        self.task = task
        self.config = config
        self.score_ga = Scoring(config)

        SearchNodeChild.UCB_CONSTANT = self.config.child_ucb_constant
        SearchNodeChild.INITIAL_VISITS_CONSTANT = self.config.child_initial_visits_constant
        Logger.VERBOSE = self.config.verbose_logging

    def timeout(self):
        return time.time() > self.start_time + self.config.time_limit

    def solve(self):
        log(f"Running task.solve() for #{self.task.task_id}")
        log(f"conf: {self.config}")

        self.start_time = time.time()

        log(f"Running task.solve() for #{self.task.task_id}")

        log("---> Initialising root")
        stop_search = self.initialise_root()
        log("<--- Done initialising root()")

        assert isinstance(stop_search, SearchStatus)

        while stop_search == SearchStatus.ContinueRunning:
            stop_search = self.tree_playout()
            log(f"stop_search: {stop_search}")

        solving_time = time.time() - self.start_time

        return solving_time, stop_search

    def initialise_root(self):
        """
        initialises the root node of search tree for each abstraction
        """

        f = factory.AbstractionFactory()
        self.abstraction_bundles = f.create_all(self.task, self.config.abstractions)
        log(f"using abstraction_bundles: {self.abstraction_bundles.keys()}")

        self.all_anodes = []
        self.worst_original_score = -1
        self.tree_playouts = 0
        for abstraction, task_bundle in self.abstraction_bundles.items():

            log(f"Doing abstraction: {abstraction}")

            assert task_bundle.abstraction == abstraction
            anode = AbstractionNode(task_bundle)
            self.all_anodes.append(anode)

            s0 = time.time()

            in_bundle = anode.orig_input_bundle()

            original_score, _ = self.score_ga(anode, in_bundle.copy())
            self.worst_original_score = max(original_score, self.worst_original_score)

            parent_node = anode
            anode.root_node = self.expand_node(anode, in_bundle, parent_node)

            s1 = time.time()
            log(f"expand_node() time_taken: {s1 - s0:.2f}")

            log(f"Initial root node for {anode.abstraction}, worst_score: {self.worst_original_score}")
            anode.root_node.dump(10)
            anode.visits = self.config.child_initial_visits_constant
            self.tree_playouts += 1
            if anode.best_score == 0:
                return SearchStatus.SolutionFound

            if self.timeout():
                return SearchStatus.TimeoutInitialiseRoot

        return SearchStatus.ContinueRunning

    def select_child(self, node):
        # this does a uct update
        node.update()
        return node.children[0]

    def select_child_visits(self, node):
        best_child = None
        for c in node.children:
            if best_child is None:
                best_child = c
            elif c.visits > best_child.visits:
                best_child = c
            elif c.visits == best_child.visits and c.score < best_child.score:
                best_child = c
        return best_child

    def select_abstraction_node(self):
        best_anode = None
        best_score = None
        for anode in self.all_anodes:
            normalised_score = 1.0 - anode.best_score / anode.root_node.original_score
            exploration = (self.config.child_ucb_constant *
                           math.sqrt(math.log(self.tree_playouts + 1) / (anode.visits)))

            score = normalised_score + exploration
            if best_anode is None or score > best_score:
                best_score = score
                best_anode = anode

            log(f" --- {anode.abstraction} {anode.visits} {anode.best_score}" +
                f" -- {normalised_score:.2f} + {exploration:.2f} == {score:.2f}")

        log(f"choose {best_anode.abstraction}")
        return best_anode

    def tree_playout(self):
        """
        perform one iteration of search for a solution
        """

        cur_anode = self.select_abstraction_node()
        cur_node = cur_anode.root_node

        in_bundle = cur_anode.orig_input_bundle()
        while True:
            cur_node.incr_visits()

            if not cur_node.finished_expanding():
                self.continue_expand_node(cur_anode, cur_node, in_bundle)
                self.backpropagate_score(cur_node)
                if cur_node.best_score == 0:
                    break

                # ok continue to select child

            # special case - where there are no children left
            if not cur_node.children:
                self.backpropagate_score(cur_node)
                break

            child = self.select_child(cur_node)
            child.incr_visits()

            # move state forward
            changed = False
            for ga in in_bundle:
                if parameters.apply_instruction(ga, child.instruction):
                    changed = True
            assert changed

            # only on reruns (maybe set a flag and assert this)
            assert child.score != 0

            if child.next is not None:
                cur_node = child.next
            else:
                res = self.expand_node(cur_anode, in_bundle, child)
                child.next = res
                self.backpropagate_score(res)
                break

        # update stats
        self.tree_playouts += 1
        cur_anode.visits += 1

        log(f"Root after {self.tree_playouts} playouts")

        cur = cur_anode.root_node
        for i in range(3):
            prefix = "..." * i + " "
            cur.dump(10, prefix=prefix)

            c = self.select_child_visits(cur)
            if c is None or not c.next:
                break
            log(f"{prefix}next node {c.instruction}")
            cur = c.next

        if cur_anode.root_node.best_score == 0:
            return SearchStatus.SolutionFound

        if self.timeout():
            return SearchStatus.NoSolutionFound

        return SearchStatus.ContinueRunning

    def expand_node(self, anode, in_bundle, parent_node):
        """ expand one node """

        log(f"Expanding with abstraction '{anode.abstraction}'")

        ###############################################################################
        # create a node

        original_score, token = self.score_ga(anode, in_bundle.copy())
        node = SearchTreeNode(parent_node, original_score)
        anode.add_token_to_seen(token)

        ###############################################################################
        # candidate filters
        s0 = time.time()

        # updated_bundle is not modified here
        filters_instrs = filters.get_candidate_filters(in_bundle,
                                                       self.config.do_combined_filters)
        s1 = time.time()
        log(f"get_candidate_filters() time_taken: {s1 - s0:.2f}, # {len(filters_instrs)}")

        # stats:
        anode.stats.total_filter_instructions += len(filters_instrs)
        node.total_filter_instructions = len(filters_instrs)

        ###############################################################################
        # candidate transformations

        transformations = tconfig.get_ops(anode.abstraction)

        s0 = time.time()
        tis = list(trans.get_all_transformations(transformations, in_bundle))

        all_instructions = []
        for fis in filters_instrs:
            dyn_params = parameters.generate_dynamic_params(fis, in_bundle)
            for ti in tis:
                if ti.has_param_binding():
                    for pbi in dyn_params:
                        # only added if both ti.has_param_binding() and dyn_params has values
                        all_instructions.append(Instruction(fis, ti, pbi))
                else:
                    all_instructions.append(Instruction(fis, ti))

        s1 = time.time()
        log(f" {s1 - s0:.2f} secs -- #tis {len(tis)} / *instrs {len(all_instructions)}")

        s0 = time.time()

        anode.stats.total_instructions += len(all_instructions)
        node.total_instructions = len(all_instructions)

        node.todo_instructions.extend(all_instructions)
        if node.todo_instructions:
            self.continue_expand_node(anode, node, in_bundle)

        if node.finished_expanding():
            if self.config.prune_worse_scores:
                node.prune_worse(self.config)

        s1 = time.time()

        log(f"create_child() {s1 - s0:.2f} secs -- Number of new children added = {len(node.children)}")

        return node

    def continue_expand_node(self, anode, node, in_bundle):

        assert node.todo_instructions

        ###############################################################################
        # create a child per instruction, and score each one

        for ii in range(self.config.expand_children_max):
            if not node.todo_instructions:
                break

            instruction = node.todo_instructions.popleft()

            child_node = self.create_child(anode, instruction, in_bundle.copy(), node)
            if child_node is None:
                continue

            # XXX the problem here is that we might remove good rules
            # also for the hashing, we should at least store the instruction for later
            # XXX idea: maybe pruned and use progressive widening
            if self.config.do_hashing:
                if anode.check_seen_token(child_node.token):
                    # maybe add to pruned
                    continue

                anode.add_token_to_seen(child_node.token)

            node.add(child_node)
            anode.stats.total_children_added += 1
            node.best_score = min(node.best_score, child_node.score)

            if node.best_score == 0:
                log("Early break expanding children, since found solution")
                break

            # breakout early?
            if self.timeout():
                break

    def create_child(self, anode, instr, in_bundle, parent_node):
        try:
            changed = False
            for ga in in_bundle:
                if parameters.apply_instruction(ga, instr):
                    changed = True
            if not changed:
                return None

        except Exception as e:
            if self.config.verbose_create_child:
                #  we need to hande this better somehow, i mean why have errors at all?
                log(f"XXX Failed to apply: {instr}, because: {e}")
                _, _, tb = sys.exc_info()
                traceback.print_exc()
            e = e
            anode.stats.errors_creating_child += 1
            return None

        score, token = self.score_ga(anode, in_bundle)
        if score == -1 or token == -1:
            anode.stats.errors_creating_child += 1
            return None

        anode.stats.total_instructions += 1
        return SearchNodeChild(instr, parent_node, score, token)

    def backpropagate_score(self, node: SearchTreeNode):
        log(f"backpropagate node: {node}")

        while True:
            log(f"+NODE scores: {node.original_score} / {node.best_score}")
            child_or_end = node.back_link
            # might be better to use None here...
            if isinstance(child_or_end, AbstractionNode):
                log("+ROOT")
                # the end...
                break

            child = child_or_end

            assert isinstance(child, SearchNodeChild)
            best_score = min(node.original_score, node.best_score, child.score)
            log(f"+CHILD {child} {child.score} --> {best_score}")

            child.score = best_score
            node = child.search_tree_node
            # update will update the nodes score to the best child
            node.update()
            assert node.best_score <= best_score

    def get_best_instructions(self):
        """
        apply solution abstraction and apply_call to test image
        """

        # get the best abstraction node
        best_anode = None
        for anode in self.all_anodes:
            if best_anode is None or anode.best_score < best_anode.best_score:
                best_anode = anode

        cur = best_anode.root_node
        instructions = []
        while cur is not None:
            best_child = None
            for c in cur.children:
                if best_child is None or c.score < best_child.score:
                    best_child = c

            assert best_child
            instructions.append(best_child.instruction)
            cur = best_child.next

        return best_anode, instructions

    def apply_solution(self, in_grid, anode, instructions):
        ga = factory.AbstractionFactory().create(anode.abstraction, in_grid)

        # move state forward
        try:
            for instr in instructions:
                parameters.apply_instruction(ga, instr)

        except Exception as e:
            log(f"apply_solution() failed at: {instr}, because: {e}")
            _, _, tb = sys.exc_info()
            traceback.print_exc()
            return None

        reconstructed = ga.undo_abstraction()
        return reconstructed
