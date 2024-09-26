from collections import Counter

from itertools import combinations

from common.grid import Grid


# only have one PatternObject. In theory there are 3 types of pattern object

# patch - a 2d rectange of grid
# coords - single colour, with background
# coords - multi colour, with background

# by using the representation of multi-coloured, we can representation the other two type.  we can
# then augment the patterns with attributes and relations, of which is_uni_coloured and is_patch
# are now important.

# the graph view is just the same a logic view:
#  1.  attributes on a object are attributes on a single node
#  2.  relations between objects are edges between nodes

class PatternObject:
    def __init__(self, index, colour_coords):
        self.index = index
        self.colour_coords = colour_coords

        self.edges = []

        # lazily computed
        self.cached_shape = None

    @property
    def size(self):
        return len(self.colour_coords)

    @property
    def is_unicolour(self):
        return len(self.colours() == 1)

    @property
    def is_mulitcolour(self):
        return len(self.colours() > 1)

    @property
    def is_patch(self):
        _, _, x, y = self.bounding_box()
        area = x * y
        return len(self.coords) == area

    def colours(self):
        all_colours = [c for c, _ in self.colour_coords]
        return set(all_colours)

    def most_common_colour(self):
        all_colours = [c for c, _ in self.colour_coords]
        return max(self.colours, key=all_colours.count)

    def reset_edges(self):
        self.edges = []

    def coords(self):
        return [coord for _, coord in self.colour_coords]

    def safe_coords(self, ga):
        return [coord for _, coord in self.colour_coords if ga.coord_in_ga(coord)]

    def safe_colour_coords(self, ga):
        return [(colour, coord) for colour, coord in self.colour_coords if ga.coord_in_ga(coord)]

    def degree(self):
        return len(self.edges)

    def add_edge(self, other, attribute):
        self.edges.append((other, attribute))

    def has_edge(self, other):
        for o, what in self.edges:
            if o == other:
                return what
        return None

    def neighbours(self):
        return [obj for obj, _ in self.edges]

    def get_signature_shape(self):
        """
        get the shape of the object.
        This works by taking the ith and jth coordinate closest to origin (0, 0) and then moving
        the entire shape that way.
        """
        if self.cached_shape:
            return self.cached_shape

        coords = self.coords
        if len(coords) == 0:
            return set()
        min_i = min(i for i, j in coords)
        min_j = min(j for i, j in coords)

        self.cached_shape = tuple(sorted((i - min_i, j - min_j) for i, j in coords))
        return self.cached_shape

    def bounding_box(self):
        coords = self.coords()

        # XXX optimisation: could do one loop here
        min_i, min_j = min(i for i, _ in coords), min(j for _, j in coords)
        max_i, max_j = max(i for i, _ in coords), max(j for _, j in coords)
        return (min_i, min_j, max_i - min_i + 1, max_j - min_j + 1)

    def update(self):
        # if we updated any attributes, we need to fix things up.  Do that here.
        # in c++ we will be able to make this immutable or at least const will know what is going on
        self.cached_shape = None

    def __repr__(self):
        return get_signature_string(self)


class GraphAbstraction:
    def __init__(self, grid, abstraction_type=None, **attributes):
        # store anything useful here
        self.attributes = attributes

        # make sure we are have a grid
        grid = self.original_grid = Grid(grid)

        # important, the original grid can get out of sync if we modify the underlying objects
        self.abstraction_type = abstraction_type

        self.height, self.width = grid.shape
        assert self.height > 0 and self.width > 0

        self.shape = grid.shape

        # basically a 1d array of each row
        self.array_1d = []

        for row in grid:
            for colour in row:
                self.array_1d.append(colour)

        self.really_most_common_colour = max(self.array_1d, key=self.array_1d.count)

        self.pattern_objs_dict = {}

        # background is zero until told otherwise
        self.set_background_colour(0)

    def set_background_colour(self, colour):
        self.background_colour = colour

    @property
    def corners(self):
        return {(0, 0), (0, self.width - 1),
                (self.height - 1, 0), (self.height - 1, self.width - 1)}

    @property
    def all_colours(self):
        array_1d_no_bg = [c for c in self.array_1d if c != self.background_colour]
        # handle weird cases when grid all one colour
        if not array_1d_no_bg:
            return set(self.array_1d)
        return set(array_1d_no_bg)

    @property
    def most_common_colour(self):
        array_1d_no_bg = [c for c in self.array_1d if c != self.background_colour]
        return max(self.all_colours, key=array_1d_no_bg.count)

    @property
    def least_common_colour(self):
        array_1d_no_bg = [c for c in self.array_1d if c != self.background_colour]
        return min(self.all_colours, key=array_1d_no_bg.count)

    def all_colours_for_filters(self):
        colours = set()
        for o in self.objs:
            colours.update(o.colours)
        return colours

    def coord_in_ga(self, coord):
        ii, jj = coord
        if ii < 0 or jj < 0:
            return False
        if ii >= self.height or jj >= self.width:
            return False
        return True

    @property
    def objs(self):
        return list(self.pattern_objs_dict.values())

    def indices(self):
        ''' return indices '''
        return list(self.pattern_objs_dict)

    def items(self):
        return [(k, v) for k, v in self.pattern_objs_dict.items()]

    def get_obj(self, index):
        return self.pattern_objs_dict[index]

    def all_cords_as_frozen_sets(self):
        return {frozenset(o.coords) for o in self.pattern_objs_dict.values()}

    def pixel_assignments(self):
        ''' returns which each pixel has an object pointing to '''
        assignments = dict()

        for obj in self.objs:
            for o, c in obj.colour_coords:
                assignments.setdefault(c, []).append(obj)
        return assignments

    def undo_abstraction(self) -> Grid:
        # XXX handles overlaps, but there is no logic behind it
        grid_list = [[-1 for r in range(self.width)] for _ in range(self.height)]

        assignments = self.pixel_assignments()

        overlap_method = True
        for _, objs in assignments.items():
            if len(objs) > 1:
                # print("WARNING, overlapping objects during undo_abstraction()")
                overlap_method = False
                break

        if overlap_method:
            # no overlapping - this is much faster
            for obj in self.objs:
                for col, (ii, jj) in obj.safe_colour_coords(self):
                    grid_list[ii][jj] = col
        else:
            for (i, j), objs in assignments.items():
                for obj in objs:
                    obj = objs[0]
                    if (i, j) not in obj.safe_coords(self):
                        continue

                    for col, (ii, jj) in obj.safe_coords(self):
                        if ii == i and jj == j:
                            if grid_list[i][j] == -1:
                                grid_list[i][j] = col

        # replace anything left with -1 with background_colour or 0.
        bg = max(self.background_colour, 0)
        new_rows = []
        for row in grid_list:
            new_row = []
            for c in row:
                if c == -1:
                    new_row.append(bg)
                else:
                    new_row.append(c)
        
        return Grid(grid_list)

    def fix_up_attrs(self):
        ''' huge hack - cause we have serious problem with transformations only update objects '''
        grid = self.undo_abstraction()

        # basically a 1d array of each row
        self.array_1d = []

        for row in grid:
            for colour in row:
                self.array_1d.append(colour)

        most_common_colour = max(self.all_colours, key=self.array_1d.count)
        self.really_most_common_colour = most_common_colour

    def copy(self):
        assert self.abstraction_type is not None
        grid = self.undo_abstraction()
        g = GraphAbstraction(grid, self.abstraction_type)

        g.set_background_colour(self.background_colour)

        for o in self.objs:
            g.add_object(o.index, copy_object(o))

        g.update_abstracted_graph()
        return g

    def update_abstracted_graph(self):
        """
        update the abstracted graphs so that they remain consistent after a transformation

        this will handle
        - removing objects
        - inserting objects
        - updating objects
        """
        # XXX just throw away all the edges, and recreate?

        from mcarga.abstractions.factory import Builder

        # another horrific hack, just remove and rebuild all the edges
        for obj in self.objs:
            obj.reset_edges()

        assignments = self.pixel_assignments()
        for coord, objs in assignments.items():
            if len(objs) > 1:
                for obj0, obj1 in combinations(self.objs, 2):
                    if obj0.has_edge(obj1) != "overlap":
                        obj0.add_edge(obj1, "overlap")
                        obj1.add_edge(obj0, "overlap")

        bob = Builder(self)
        for obj0, obj1 in combinations(self.objs, 2):
            # dont add edge if overlap already added
            if obj0.has_edge(obj1) == "overlap":
                continue

            bob.add_edge(obj0, obj1, self.background_colour)

    ###############################################################################
    # checks

    def check_within_grid(self, *coords):
        """
        check if given coords are all within the grid boundary
        """

        for i, j in coords:
            if i < 0 or j < 0 or i >= self.height or j >= self.width:
                return False
        return True

    def check_collision(self, obj, *coords):
        """
        check if given coords collide with any other objects in the graph (but not obj)
        returns True if collides.
        """
        coords = set(coords)
        for other in self.objs:
            if obj is other:
                continue

            if len(set(other.coords) & coords) != 0:
                # print(f"collided with {other}")
                return True
        return False

    def check_pixel_occupied(self, coord):
        """ check if a pixel is occupied by any object in the graph """

        for obj in self.objs:
            for c in obj.coords:
                if c == coord:
                    return True
        return False

    def remove_object(self, index):
        assert index in self.pattern_objs_dict
        self.pattern_objs_dict.pop(index)

    def add_object(self, index, a_obj):
        assert index not in self.pattern_objs_dict
        self.pattern_objs_dict[index] = a_obj


################################################################################

class Builder:
    def __init__(self, ga):
        self.ga = ga
        self.obj_count = Counter()

        # optimisation for add_edge()
        self.cached_grid = None

    def create_unicolour_obj(self, coords, colour):
        assert len(coords) > 0
        assert 0 <= colour < 10, f"colour: {colour} {type(colour)}"

        # a unique identifier for object, this is what it was for nx (colour, counter)
        index = (colour, self.obj_count[colour])
        self.obj_count[colour] += 1

        colour_coords = [(colour, c) for c in coords]
        new_obj = PatternObject(index, colour_coords)

        self.ga.add_object(index, new_obj)
        return index

    def create_multicolour_obj(self, colour_coords):
        assert len(colour_coords) > 0
        assert isinstance(colour_coords, list)

        size = len(colour_coords)
        index = (size, self.obj_count[size])
        self.obj_count[size] += 1

        new_obj = PatternObject(index, colour_coords)

        self.ga.add_object(index, new_obj)
        return index


################################################################################

def copy_object(o):
    return PatternObject(o.index, o.colour_coords[:])

def get_signature_string(obj):
    min_i, min_j, height, width = obj.bounding_box()

    relative_coords = sorted(f"{c},{i - min_i},{j - min_j}" for c, (i, j) in obj.colour_coords)
    res = f"PO({obj.most_common_colour})|i{min_i} j{min_j} h{height} w{width} #{obj.size}:"
    res += "|".join(relative_coords)
    return res

