'''
The code here mainly focuses on creating different types of abstractions from a grid.
Deals with the initial abstraction from pixel-level to object-level representation.

An ARC object is a group of pixels that are connected and share the same colour (based on the
abstraction method used).  An ARC multiobject similarly but supports many colours.

Object attributes:

Each node (object) has certain attributes:

colour: The colour of the pixels that make up the object.
size: The number of pixels in the object.

position: The location of the object in the grid (could be represented by its bounding box or centroid).

Edges between objects represent spatial relationships between objects in the image.

'''

from functools import partial
from collections import Counter
from itertools import combinations

from common.grid import Grid
from competition.loader import Task
from dsl import dsl_v2 as dsl

from mcarga.core import utils
from mcarga.core.alogger import log

from mcarga.statemachine.graph_abstraction import GraphAbstraction, ArcObject, ArcMultiObject


###############################################################################
# XXX replace this with left_of, right_of, below, above - and with distance

HORIZONTAL = "horizontal"
VERTICAL = "vertical"
BOTH = "both"


def connected_objects(grid: Grid, univalued: bool, diagonal: bool, bg_colour: int):
    " code based off of michod's DSL "
    objs = []
    occupied = set()
    h, w = len(grid), len(grid[0])
    unvisited = dsl.asindices(grid)
    diagfun = dsl.neighbors if diagonal else dsl.dneighbors
    for loc in unvisited:
        if loc in occupied:
            continue
        val = grid[loc[0]][loc[1]]
        if val == bg_colour:
            continue
        obj = {(val, loc)}
        cands = {loc}
        while len(cands) > 0:
            neighborhood = set()
            for cand in cands:
                v = grid[cand[0]][cand[1]]
                if (val == v) if univalued else (v != bg_colour):
                    obj.add((v, cand))
                    occupied.add(cand)
                    neighborhood |= {
                        (i, j) for i, j in diagfun(cand) if 0 <= i < h and 0 <= j < w
                    }
            cands = neighborhood - occupied
        objs.append(set(obj))
    return objs


def connected_objects_uni(grid: Grid, do_diagonals: bool, bg_colour: int):
    objs = connected_objects(grid, True, do_diagonals, bg_colour)

    # transform [(colour, coord)...] -> (colour, coords)
    result = []
    for obj in objs:
        # convert obj to list
        obj = list(obj)

        # fish colour
        colour = obj[0][0]

        # convert cords
        coords = [coord for _, coord in obj]

        result.append((colour, coords))

    return result


###############################################################################

def is_connected_horizontal(grid, obj0, obj1, bg_colour):
    height, width = grid.shape
    for i0, j0 in obj0.coords:
        if i0 < 0 or j0 < 0 or i0 >= height or j0 >= width:
            continue

        for i1, j1 in obj1.coords:
            if i1 < 0 or j1 < 0 or i1 >= height or j1 >= width:
                continue

            # two nodes on the same row
            if i0 == i1:
                # iterates through all the columns between the two points AND if all pixels
                # between these points are background colour (bg_colour), it considers this
                # to be a horizontal connection.
                distance = 1
                for column_index in range(min(j0, j1) + 1, max(j0, j1)):
                    if grid[i0, column_index] != bg_colour:
                        distance = -1
                        break
                    distance += 1

                if distance > 0:
                    return True

    return False


def is_connected_vertical(grid, obj0, obj1, bg_colour):
    height, width = grid.shape
    for i0, j0 in obj0.coords:
        if i0 < 0 or j0 < 0 or i0 >= height or j0 >= width:
            continue

        for i1, j1 in obj1.coords:
            if i1 < 0 or j1 < 0 or i1 >= height or j1 >= width:
                continue

            # two nodes on the same row
            if j0 == j1:
                # iterates through all the columns between the two points AND if all pixels
                # between these points are background colour (bg_colour), it considers this
                # to be a horizontal connection.
                distance = 1
                for row_index in range(min(i0, i1) + 1, max(i0, i1)):
                    if grid[row_index, j0] != bg_colour:
                        distance = -1
                        break
                    distance += 1

                if distance > 0:
                    return True

    return False


class Builder:
    def __init__(self, ga):
        self.ga = ga
        self.obj_count = Counter()

        # optimisation for add_edge()
        self.cached_grid = None

    def add(self, colour, coords):
        # a unique identifier for object, this is what it was for nx (colour, counter)
        index = (colour, self.obj_count[colour])
        self.obj_count[colour] += 1
        self.ga.add_object(index, ArcObject(index, coords, colour))
        self.cached_grid = None

    def add_multi(self, colour_coords):
        # a unique identifier for object, this is what it was for nx (size, counter)
        ll = len(colour_coords)
        index = (ll, self.obj_count[ll])
        self.obj_count[ll] += 1
        self.ga.add_object(index, ArcMultiObject(index, colour_coords))
        self.cached_grid = None

    def add_edge(self, obj0, obj1, bg_colour):
        if self.cached_grid is None:
            self.cached_grid = self.ga.undo_abstraction()

        horizontal = is_connected_horizontal(self.cached_grid, obj0, obj1, bg_colour)
        vertical = is_connected_vertical(self.cached_grid, obj0, obj1, bg_colour)
        if horizontal and vertical:
            obj0.add_edge(obj1, BOTH)
            obj1.add_edge(obj0, BOTH)
        elif horizontal:
            obj0.add_edge(obj1, HORIZONTAL)
            obj1.add_edge(obj0, HORIZONTAL)
        elif vertical:
            obj0.add_edge(obj1, VERTICAL)
            obj1.add_edge(obj0, VERTICAL)

    def add_edges(self):
        for obj0, obj1 in combinations(self.ga.objs, 2):
            self.add_edge(obj0, obj1, self.ga.background_colour)


class AbstractionFactory:

    def __init__(self):

        ops = {"scg": "single_connected_graph",
               "scg_nb": "single_connected_graph_no_background",
               "scg_nbc": "single_connected_graph_no_bg_corners",

               "mcg_nb": "multicolour_connected_graph_no_background",
               "vcg_nb": "vertical_connected_graph_no_background",
               "hcg_nb": "horizontal_connected_graph_no_background",

               "na": "get_no_abstraction_graph",
               #"lrg": "get_largest_rectangle_graph"
               }

        # note: mcg - would be just one big blob... so we need a background for mcg to work

        self.mapping = {}

        for name, method_name in ops.items():
            method = getattr(self, method_name)

            self.mapping[name] = method
            if name in ["scg", "scg_nb", "scg_nbc", "mcg", "mcg_nb"]:
                name = name + "_dg"
                self.mapping[name] = partial(method, do_diagonals=True)

        for i in range(3):
            score = i + 1
            next_name = f"scg_nb_s{score}"
            method = self.single_colour_connected_no_bg_scored
            self.mapping[next_name] = partial(method, required_score=score)
            next_name = next_name + "_dg"
            self.mapping[next_name] = partial(method, required_score=score, do_diagonals=True)

    ################################################################################
    # factory methods
    ################################################################################

    def single_connected_graph(self, ga: GraphAbstraction, do_diagonals=False):
        """
        return a graph abstraction of the grid, where an object/node in graph is defined as:

        a group of adjacent pixels of the same colour.  There is no distinction for background,
        which will also be returned as a group of adjacent pixels.
        """

        builder = Builder(ga)

        for colour, coords in connected_objects_uni(ga.original_grid,
                                                    do_diagonals=do_diagonals, bg_colour=-1):
            builder.add(colour, coords)

        return builder

    def single_connected_graph_no_background(self, ga: GraphAbstraction, do_diagonals=False):
        """
        return a graph abstraction of the grid, where an object/node in graph is defined as:

        a group of adjacent pixels of the same colour. excluding the background defined as the
        ga.background_colour.
        """

        builder = Builder(ga)

        for colour, coords in connected_objects_uni(ga.original_grid,
                                                    do_diagonals=do_diagonals,
                                                    bg_colour=ga.background_colour):
            builder.add(colour, coords)

        return builder

    def single_connected_graph_no_bg_corners(self, ga: GraphAbstraction, do_diagonals=False):
        """
        return a graph abstraction of the grid, where an object/node in graph is defined as:

        a group of adjacent pixels of the same colour in the original graph.
        remove nodes identified as background.
        background is defined as a node that includes a corner and has the most common colour
        """

        builder = Builder(ga)

        background = ga.really_most_common_colour

        found_a_corner = False
        for colour, coords in connected_objects_uni(ga.original_grid,
                                                    do_diagonals=do_diagonals, bg_colour=-1):
            if colour != background:
                builder.add(colour, coords)

            else:
                # background colour + contains a corner
                if len(set(coords) & ga.corners) == 0:
                    builder.add(colour, coords)
                else:
                    found_a_corner = True

        if found_a_corner:
            ga.set_background_colour(background)

        return builder

    def single_colour_connected_no_bg_scored(self, ga: GraphAbstraction, required_score: int, do_diagonals=False):
        """
        return a graph abstraction of the grid, where an object/node in graph is defined as:

        a group of adjacent pixels of the same colour in the original graph.
        remove nodes identified as background.
        background is defined as a node that includes a corner or 2 edges and has the most common colour
        """

        builder = Builder(ga)

        background = ga.really_most_common_colour

        # do a single pass and try and figure out if we background or not
        all_connected = list(connected_objects_uni(ga.original_grid,
                                                   do_diagonals=do_diagonals, bg_colour=-1))
        skip_indices = []
        for ii, (colour, coords) in enumerate(all_connected):
            # if the node touches any edge of image it is not included (which means corners too)
            score = 0
            if colour == background:
                edges = [0, 0, 0, 0]
                for i, j in coords:
                    if i == 0:
                        edges[0] = 1
                    if j == 0:
                        edges[1] = 1
                    if i == ga.height - 1:
                        edges[2] = 1
                    if j == ga.width - 1:
                        edges[3] = 1
                score = sum(edges)

            if score >= required_score:
                skip_indices.append(ii)

        if skip_indices:
            ga.set_background_colour(background)

        # 2nd pass
        for ii, (colour, coords) in enumerate(all_connected):
            if ii in skip_indices:
                continue
            builder.add(colour, coords)

        return builder

    def multicolour_connected_graph_no_background(self, ga: GraphAbstraction, do_diagonals=False):
        """
        return a graph abstraction of the grid, where an object/node in graph is defined as:

        a group of adjacent pixels of any colour, excluding background colour.

        - Each object in the resulting graph represents a "multicolour" component.

        - The colour attribute of each node is actually a list of colours, representing all the
          colours present in that component.
        """
        builder = Builder(ga)

        for colour_coords in connected_objects(ga.original_grid,
                                               False, do_diagonals, bg_colour=ga.really_most_common_colour):
            builder.add_multi(list(colour_coords))

        return builder

    def vertical_connected_graph_no_background(self, ga: GraphAbstraction):
        """
        return an abstracted graph where a node is defined as:

        a group of vertically adjacent pixels of the same colour, excluding background colour.
        """
        builder = Builder(ga)

        for colour in ga.all_colours:
            if colour == ga.background_colour:
                continue

            for fixed_y in range(ga.width):
                connected_cords = []
                for x in range(ga.height):
                    pixel = ga.original_grid[x, fixed_y]
                    if pixel != colour:
                        if connected_cords:
                            builder.add(colour, connected_cords)
                            connected_cords = []
                    else:
                        connected_cords.append((x, fixed_y))

                if connected_cords:
                    builder.add(colour, connected_cords)

        return builder

    def horizontal_connected_graph_no_background(self, ga: GraphAbstraction):
        """
        return a graph abstraction of the grid, where an object/node in graph is defined as:

        a group of horizontally adjacent pixels of the same colour, excluding background colour.
        """
        builder = Builder(ga)

        for colour in ga.all_colours:
            if colour == ga.background_colour:
                continue

            for fixed_x in range(ga.height):
                connected_cords = []
                for y in range(ga.width):
                    pixel = ga.original_grid[fixed_x, y]
                    if pixel != colour:
                        if connected_cords:
                            builder.add(colour, connected_cords)
                            connected_cords = []
                    else:
                        connected_cords.append((fixed_x, y))

                if connected_cords:
                    builder.add(colour, connected_cords)

        return builder

    def get_no_abstraction_graph(self, ga: GraphAbstraction):
        """
        return an abstracted graph where a node is defined as:
        the entire graph as one multi-colour node.
        """
        builder = Builder(ga)

        colour_coords = []
        for i, row in enumerate(ga.original_grid):
            for j, value in enumerate(row):
                pixel = ga.original_grid[i, j]
                colour_coords.append((pixel, (i, j)))

        # so looks like the others
        fake_index = (0, 0)
        ga.add_object(fake_index, ArcMultiObject(fake_index, colour_coords))

        return builder

    def create(self, abstraction_name, grid):
        assert abstraction_name in self.mapping

        grid = Grid(grid)
        ga = GraphAbstraction(grid, abstraction_type=abstraction_name)

        meth = self.mapping[abstraction_name]

        builder = meth(ga)
        builder.add_edges()

        return ga

    def create_all(self, task: Task, abstraction_names=None):

        if abstraction_names is None:
            abstraction_names = self.mapping.keys()

        # keep track of existing bundles to check for duplication - because some of the abstractions
        # can produce the same graphs (or set of objects).

        # XXX we only check if the coords are same, and not other attributes
        bundles_by_abstraction = {}

        for abstraction in abstraction_names:

            # first, produce the abstracted graphs for input output grids using the current abstraction
            # these are the 'original' abstracted graphs that will not be updated
            graphs = [self.create(abstraction, sample.in_grid)
                      for sample in task.train_samples]
            in_train_bundle = GraphBundle(graphs)

            graphs = [self.create(abstraction, sample.in_grid)
                      for sample in task.test_samples]
            in_test_bundle = GraphBundle(graphs)

            graphs = [self.create(abstraction, sample.out_grid)
                      for sample in task.train_samples]
            out_bundle = GraphBundle(graphs)

            # skip abstraction if it result in the same bundle as a previous abstraction,
            # for example: nbccg and ccgbr result in the same graphs if there is no enclosed black pixels.

            # this goes through all the graph abstractions and creates a set of frozensets of the
            # coords (for comparison)

            # XXX and even then, this isnt a fair comparison - there are other things to check like
            # colours, multi instance etc we should just have an equals method on the GA

            # XXX also note we are only testing the input bundle, the output may be different (leaving
            # this for now since output could have different dimensions and be of completely different
            # type of abstraction from input)
            input_bundle = in_train_bundle + in_test_bundle
            frozen = input_bundle.as_frozen_sets()

            # should we ignore this abstraction ?
            skip_this_abstraction = False

            # we go through the existing input bundles
            for task_bundle in bundles_by_abstraction.values():

                assert task_bundle.abstraction != abstraction
                other_in_bundle = task_bundle.input_bundle()
                other_frozen = other_in_bundle.as_frozen_sets()
                assert len(frozen) == len(other_frozen)

                all_is_equal = True
                for x, y in zip(frozen, other_frozen):
                    # XXX does this actually work?  How does ordering work in the lists?
                    if x != y:
                        all_is_equal = False
                        break

                if all_is_equal:
                    log(f"Skipping abstraction {abstraction} as it is the same as abstraction {task_bundle.abstraction}")
                    skip_this_abstraction = True
                    break

            # only add if we dont skip
            if not skip_this_abstraction:
                bundles_by_abstraction[abstraction] = TaskGraphBundle(abstraction,
                                                                      in_train_bundle,
                                                                      in_test_bundle,
                                                                      out_bundle)

        return bundles_by_abstraction


###############################################################################

class GraphBundle:
    def __init__(self, graphs):
        self.graphs = list(graphs)

    def copy(self):
        return GraphBundle(g.copy() for g in self.graphs)

    def as_frozen_sets(self):
        return [ga.all_cords_as_frozen_sets() for ga in self.graphs]

    def static_object_attributes(self, f):
        """
        Apply function f to each object across all graphs
        """
        as_set = {f(o) for ga in self.graphs for o in ga.objs}
        return list(as_set)

    def dump(self, show=True):
        for g in self.graphs:
            utils.dump(g, show=show)

    def __iter__(self):
        return iter(self.graphs)

    def __len__(self):
        return len(self.graphs)

    def __add__(self, other):
        return GraphBundle(self.graphs + other.graphs)


class TaskGraphBundle:
    def __init__(self, abstraction, in_train_bundle, in_test_bundle, out_bundle):
        self.abstraction = abstraction
        self.in_train_bundle = in_train_bundle
        self.in_test_bundle = in_test_bundle
        self.out_bundle = out_bundle

    def input_bundle(self):
        return self.in_train_bundle + self.in_test_bundle

    def pairs(self):
        assert len(self.in_train_bundle) == len(self.out_bundle)
        return zip(self.in_train_bundle, self.out_bundle)


