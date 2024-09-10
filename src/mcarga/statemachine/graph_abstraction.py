
# XXX there is some code duplication here.  See experimental/arc_object.py for alternative implementation.


from itertools import combinations

from common.grid import Grid


class ArcObject:
    def __init__(self, index, coords, colour):
        self.index = index
        self.coords = coords
        self.colour = colour

        # might need to be obj -> {}
        self.edges = []

        # lazily computed
        self.cached_shape = None

    # keeping ArcObject/ArcMultiObject interface aligned
    @property
    def most_common_colour(self):
        return self.colour

    @property
    def colours(self):
        return [self.colour]

    @property
    def size(self):
        return len(self.coords)

    def reset_edges(self):
        self.edges = []

    def safe_coords(self, ga):
        return [coord for coord in self.coords if ga.coord_in_ga(coord)]

    @property
    def degree(self):
        return len(self.edges)

    def add_edge(self, other, attribute):
        assert isinstance(other, ArcObject)
        self.edges.append((other, attribute))

    def has_edge(self, other):
        assert isinstance(other, ArcObject)
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
        coords = self.coords
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


class ArcMultiObject:
    def __init__(self, index, colour_coords):
        self.index = index
        self.colour = -1
        self.colour_coords = colour_coords

        self.edges = []

        # lazily computed
        self.cached_shape = None

    @property
    def colours(self):
        all_colours = [c for c, _ in self.colour_coords]
        return set(all_colours)

    @property
    def most_common_colour(self):
        all_colours = [c for c, _ in self.colour_coords]
        return max(self.colours, key=all_colours.count)

    @property
    def size(self):
        return len(self.colour_coords)

    def reset_edges(self):
        self.edges = []

    @property
    def coords(self):
        return [coord for _, coord in self.colour_coords]

    def safe_coords(self, ga):
        return [coord for _, coord in self.colour_coords if ga.coord_in_ga(coord)]

    def safe_colour_coords(self, ga):
        return [(colour, coord) for colour, coord in self.colour_coords if ga.coord_in_ga(coord)]

    @property
    def degree(self):
        return len(self.edges)

    def add_edge(self, other, attribute):
        assert isinstance(other, ArcMultiObject)
        self.edges.append((other, attribute))

    def has_edge(self, other):
        assert isinstance(other, ArcMultiObject)
        for o, what in self.edges:
            if o == other:
                return what
        return None

    def as_coords(self):
        return [c for _, c in self.colour_coords]

    def neighbours(self):
        for obj, _ in self.edges:
            yield obj

    def get_signature_shape(self):
        """
        get the shape of the object
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
        coords = self.coords

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


def copy_object(o):
    if isinstance(o, ArcObject):
        new_o = ArcObject(o.index, o.coords[:], o.colour)
    else:
        assert isinstance(o, ArcMultiObject)
        new_o = ArcMultiObject(o.index, o.colour_coords[:])

    return new_o


class GraphAbstraction:
    # set on SearchPerAbstraction - in search.py (XXX hack for now)
    is_training_graph = True

    def __init__(self, grid, abstraction_type=None):

        # make sure we are have a grid
        grid = self.original_grid = Grid(grid)

        # important, the original grid can get out of sync if we modify the underlying objects

        self.abstraction_type = abstraction_type

        self.height, self.width = grid.shape
        assert self.height > 0 and self.width > 0

        self.shape = grid.shape

        # this should be a property
        self.corners = {(0, 0), (0, self.width - 1),
                        (self.height - 1, 0), (self.height - 1, self.width - 1)}

        # all objects - simply as dict
        multicolour_abstractions = ["mcg_nb", "na"]
        self.is_multicolour = self.abstraction_type in multicolour_abstractions

        # basically a 1d array of each row
        self.array_1d = []

        for row in grid:
            for colour in row:
                self.array_1d.append(colour)

        self.really_most_common_colour = max(self.array_1d, key=self.array_1d.count)

        self.arc_objs_dict = {}

        # background is zero until told otherwise
        self.set_background_colour(0)

    def set_background_colour(self, colour):
        self.background_colour = colour

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
        return list(self.arc_objs_dict.values())

    def indices(self):
        ''' return indices '''
        return list(self.arc_objs_dict)

    def items(self):
        return [(k, v) for k, v in self.arc_objs_dict.items()]

    def get_obj(self, index):
        return self.arc_objs_dict[index]

    def all_cords_as_frozen_sets(self):
        return {frozenset(o.coords) for o in self.arc_objs_dict.values()}

    def pixel_assignments(self):
        ''' returns which each pixel has an object pointing to '''
        assignments = dict()

        for obj in self.objs:
            for c in obj.coords:
                assignments.setdefault(c, []).append(obj)
        return assignments

    def undo_abstraction(self) -> Grid:
        # XXX this doesnt handle overlaps
        bg_colour = max(0, self.background_colour)
        grid_list = [[bg_colour for r in range(self.width)] for _ in range(self.height)]

        assignments = self.pixel_assignments()

        fast_method = True
        for _, objs in assignments.items():
            if len(objs) > 1:
                # print("WARNING, overlapping objects during undo_abstraction()")
                fast_method = False

        if fast_method:
            # no overlapping
            for obj in self.objs:
                if isinstance(obj, ArcMultiObject):
                    for col, (ii, jj) in obj.safe_colour_coords(self):
                        grid_list[ii][jj] = col
                else:
                    assert isinstance(obj, ArcObject)
                    for ii, jj in obj.safe_coords(self):
                        grid_list[ii][jj] = obj.colour
        else:
            # print("SLOW METHOD")
            for (i, j), objs in assignments.items():
                for obj in objs:
                    obj = objs[0]
                    if (i, j) not in obj.safe_coords(self):
                        continue

                    if isinstance(obj, ArcMultiObject):
                        for col, (ii, jj) in obj.safe_coords(self):
                            if ii == i and jj == j:
                                grid_list[i][j] = col

                    else:
                        assert isinstance(obj, ArcObject)
                        grid_list[i][j] = obj.colour

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

    def add_object(self, index, a_obj):
        assert index not in self.arc_objs_dict
        self.arc_objs_dict[index] = a_obj

    def remove_object(self, index):
        assert index in self.arc_objs_dict
        self.arc_objs_dict.pop(index)

    def create_single_obj(self, coords, colour):
        """
        Creates a new ArcObject for single-colour abstractions.

        Args:
        coords: List of (i, j) coordinates for the object

        Returns:
        The newly created ArcObject
        """

        assert len(coords) > 0
        assert 0 <= colour < 10, f"colour: {colour} {type(colour)}"

        if self.is_multicolour:
            raise ValueError("This method is for single-color abstractions only")

        next_id = max((idx for c, idx in self.indices() if c == colour), default=-1) + 1
        index = (colour, next_id)
        new_obj = ArcObject(index, coords, colour)
        self.add_object(index, new_obj)
        return index

    def create_multi_obj(self, colour_coords):
        """
        Creates a new ArcMultiObject for multi-color abstractions.

        Args:
        colour_coords: List of (colour, (i, j)) tuples for the object

        Returns:
        The newly created ArcMultiObject
        """
        assert len(colour_coords) > 0
        assert isinstance(colour_coords, list)

        if not self.is_multicolour:
            raise ValueError("This method is for multi-color abstractions only")

        size = len(colour_coords)
        next_id = max((idx for s, idx in self.indices() if s == size), default=-1) + 1
        index = (size, next_id)
        new_obj = ArcMultiObject(index, colour_coords)
        self.add_object(index, new_obj)
        return index


################################################################################

def get_signature_string(obj):
    min_i, min_j, height, width = obj.bounding_box()

    relative_coords = sorted(f"{i - min_i},{j - min_j}" for i, j in obj.coords)
    obj_type_str = "AO" if isinstance(obj, ArcObject) else "AMO"
    res = f"{obj_type_str}({obj.most_common_colour})|i{min_i} j{min_j} h{height} w{width} #{obj.size}:"
    res += "|".join(relative_coords)
    return res

