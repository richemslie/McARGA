# only have one ArcObject, handle representation under the hood

# the idea is that transformations etc would all act on the highest level here (which would the multilevel interface)


class SingleUnderlying:
    def __init__(self, coords, colour):
        self.coords = coords
        self.colour = colour


class MultiDataUnderlying:
    def __init__(self, colour_coords):
        self.colour_coords = colour_coords

        all_colours = [c for c, _ in colour_coords]
        self.colours = set(all_colours)
        self.most_common_colour = max(self.colours, key=all_colours.count)

        # precompute this, accessed a lot
        self.coords = [coord for _, coord in colour_coords]

    # XXX leftover
    def safe_colour_coords(self, ga):
        return [(colour, coord) for colour, coord in self.colour_coords if ga.coord_in_ga(coord)]


class ArcObject:
    def __init__(self, index, multi=None, single=None):
        self.index = index

        assert (self.multi is None) != (self.single is None), "only one of the above should be set"

        self.multi = multi
        self.single = single

        # might need to be obj -> {}
        self.edges = []

        # lazily computed
        self.cached_sig_shape = None

    # multi/single  -------------------------------------------------------------------------------
    # XXX only these functions access underlying directly -- we could still use inheritance here
    @property
    def is_multi_coloured(self):
        return self.multi is not None

    # one interface to rule them all
    @property
    def most_common_colour(self):
        if self.multi:
            return self.multi.most_common_colour
        else:
            return self.single.colour

    @property
    def colours(self):
        if self.multi:
            return self.multi.colours
        else:
            return [self.single.colour]

    @property
    def coords(self):
        if self.multi:
            return self.multi.coords
        else:
            return self.single.coords

    # universal -------------------------------------------------------------------------------

    @property
    def size(self):
        return len(self.coords)

    # XXX the jury is still out on this one
    def safe_coords(self, ga):
        return [coord for coord in self.coords if ga.coord_in_ga(coord)]

    # edge related -------------------------------------------------------------------------------
    def reset_edges(self):
        self.edges = []

    @property
    def degree(self):
        return len(self.edges)

    def add_edge(self, other: "ArcObject", attribute):
        self.edges.append((other, attribute))

    def has_edge(self, other: "ArcObject"):
        for o, what in self.edges:
            if o == other:
                return what
        return None

    def neighbours(self):
        return [obj for obj, _ in self.edges]

    def get_signature_shape(self):
        """get the shape of the object, by shifting coords to origin (0, 0).

        returns a sorted tuple, can be used for comparisons or hashing (indexing in a dictionary
        for example)
        """
        if self.cached_sig_shape:
            return self.cached_sig_shape

        coords = self.coords
        if len(coords) == 0:
            return set()
        min_i = min(i for i, j in coords)
        min_j = min(j for i, j in coords)

        self.cached_sig_shape = tuple(sorted((i - min_i, j - min_j) for i, j in coords))
        return self.cached_sig_shape

    def update(self):
        # if we updated any attributes, we need to fix things up.  Do that here.
        # in c++ we will be able to make this immutable or at least const will know what is going on
        self.cached_shape = None

    def __repr__(self):
        return get_signature_string(self)


def get_signature_string(obj):
    min_i, min_j, height, width = obj.bounding_box()

    relative_coords = sorted(f"{i - min_i},{j - min_j}" for i, j in obj.coords)
    obj_type_str = "AO" if isinstance(obj, ArcObject) else "AMO"
    return f"{obj_type_str}({obj.most_common_colour})|i{min_i} j{min_j} h{height} w{width} #{obj.size}:" + "|".join(relative_coords)



