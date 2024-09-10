from mcarga.core.definitions import Direction, RelativePosition

from mcarga.gen_values import PossibleValuesDynamicParams, ParamBindingArg
from mcarga.instruction import ParamBindingInstruction
from mcarga.selection.filters import Filters, apply_filters
from mcarga.transformations.transformations import Transformations


class ParameterBinding:
    param_binding_ops = ["neighbour_by_size", "neighbour_by_colour"]

    def __init__(self, ga):
        self.ga = ga
        self.the_filterer = Filters(ga)

    def neighbour_by_colour(self, index, colour):
        """
        returns the first neighbour of an object satisfying given colour filter
        """
        obj = self.ga.get_obj(index)
        unique = None
        for neighbour in obj.neighbours():
            if self.the_filterer.by_colour(neighbour.index, colour, exclude=False):
                if unique is not None:
                    return None
                unique = neighbour.index
        return unique

    def neighbour_by_size(self, index, size):
        """
        returns the first neighbour of an object satisfying given size filter
        """
        obj = self.ga.get_obj(index)
        unique = None
        for neighbour in obj.neighbours():
            if self.the_filterer.by_size(neighbour.index, size, exclude=False):
                if unique is not None:
                    return None
                unique = neighbour.index
        return unique


def generate_dynamic_params(fis, input_bundle):
    VERBOSE = False

    # precompute this:
    filtered_objects_per_graph = []
    for ga in input_bundle:

        filtered_objects = []

        # for each object
        for index in ga.indices():
            if apply_filters(fis, ga, index):
                filtered_objects.append(index)

        if not filtered_objects:
            return []

        filtered_objects_per_graph.append(filtered_objects)

    if VERBOSE:
        print("GDP: Filtered objects", filtered_objects_per_graph)

    all_possible_values = []
    filtered_nodes_all = []

    for param_binding_op in ParameterBinding.param_binding_ops:
        func = getattr(ParameterBinding, param_binding_op)
        pv = PossibleValuesDynamicParams(func, input_bundle)
        for param_vals in pv.product_of():

            applicable_to_all = True
            param_bind_nodes = []

            # for each set of filtered_objects per_graph
            for filtered_objects, ga in zip(filtered_objects_per_graph, input_bundle):
                param_bind_nodes_i = []

                assert len(filtered_objects) > 0

                pb = ParameterBinding(ga)

                # test filter per object
                for obj_index in filtered_objects:
                    # actually call the param binding function
                    func = getattr(pb, param_binding_op)
                    bound_object_index = func(obj_index, **param_vals)

                    result_str = "+" if bound_object_index is not None else "-"
                    if VERBOSE:
                        print(f"GDP trying {result_str} {param_binding_op}({obj_index}, **{param_vals})")

                    if bound_object_index is None:
                        # unable to find node for filtered node to bind parameter to
                        applicable_to_all = False
                        break

                    param_bind_nodes_i.append(bound_object_index)

                if len(param_bind_nodes_i) == 0:
                    applicable_to_all = False

                if not applicable_to_all:
                    break

                param_bind_nodes.append(param_bind_nodes_i)

            # XXX param_bind_nodes needs to be sorted - check on other one
            if applicable_to_all:
                dupe = param_bind_nodes in filtered_nodes_all
                if VERBOSE:
                    print(f"GDP - YES: {param_bind_nodes} dupe: {dupe}")
                if not dupe:
                    all_possible_values.append(ParamBindingInstruction(param_binding_op, param_vals))
                    filtered_nodes_all.append(param_bind_nodes)

    if VERBOSE:
        print(f"GDP - all_possible_values: {all_possible_values}")
    return all_possible_values


def apply_instruction(ga, ii):
    ''' returns False if no transformation applied. otherwise returns True.
     !! WILL MODIFY ga !!! '''
    VERBOSE = False

    if VERBOSE:
        print(f"IN: {ga}")
        print(f"IN: {ii}")

    tt = Transformations(ga)
    func = getattr(tt, ii.ti.name)

    def func_wrapper(index, **kwds):
        params_str = ", ".join(f"{k}={v}" for k, v in kwds.items())
        if VERBOSE:
            print(f"CALLING {ii.ti.name}({index} {params_str})")
        return func(index, **kwds)

    # for each object
    filtered_objs = [index for index in ga.indices() if apply_filters(ii.fis, ga, index)]
    if VERBOSE:
        print(f"filtered_objs {filtered_objs}")

    if not ii.is_param_binding_set():
        # note func_wrapper() is mainly for side effects in transforming ga.

        # this cannot be set if instruction is not set
        assert not ii.ti.has_param_binding()

        changed = False
        for index in filtered_objs:
            if func_wrapper(index, **ii.ti.params):
                changed = True

        if not changed:
            return False

    else:
        # this cannot be set if instruction is not set
        assert ii.ti.has_param_binding()
        assert isinstance(ii.param_binding_instruction, ParamBindingInstruction)

        pbi = ii.param_binding_instruction

        for index in filtered_objs:
            call_with_params = {}

            for k, v in ii.ti.params.items():
                if isinstance(v, ParamBindingArg):
                    v = bind_parameters(index, ga, pbi, k)

                call_with_params[k] = v

            func_wrapper(index, **call_with_params)

    # update the edges in the abstracted graph to reflect the changes
    ga.update_abstracted_graph()
    ga.fix_up_attrs()
    return True


def get_relative_pos(ga, index0, index1):
    """ direction of where object at index1 is relative to index0
  , ie what is the direction going from 2 to 1
    """
    obj0 = ga.get_obj(index0)
    obj1 = ga.get_obj(index1)

    best = None
    for i0, j0 in obj0.coords:
        for i1, j1 in obj1.coords:

            # Calculate the differences
            di = i1 - i0
            dj = j1 - j0

            # Check horizontal and vertical directions
            # will replace best if already set
            if di == 0:
                if dj > 0:
                    best = Direction.RIGHT
                elif dj < 0:
                    best = Direction.LEFT
            elif dj == 0:
                if di < 0:
                    best = Direction.UP
                elif di > 0:
                    best = Direction.DOWN

            # Check diagonal directions

            # This ensures reachability for diagonals
            # note best is only set if not already set
            elif best is None and abs(di) == abs(dj):
                if di < 0 and dj > 0:
                    best = Direction.UP_RIGHT
                elif di < 0 and dj < 0:
                    best = Direction.UP_LEFT
                elif di > 0 and dj > 0:
                    best = Direction.DOWN_RIGHT
                elif di > 0 and dj < 0:
                    best = Direction.DOWN_LEFT

    return best


def get_centroid_from_coords(coords):
    """
    This function calculates the centroid (geometric center) of a list of pixel coordinates.
    """

    # sums up all the x-coordinates (i) and y-coordinates (j) separately.
    # adds half the number of coordinates to each sum to round up.
    # It then divides each sum by the total number of coordinates to get the average.

    sz = len(coords)
    center_i = (sum(i for i, _ in coords) + sz // 2) // sz
    center_j = (sum(j for _, j in coords) + sz // 2) // sz
    return center_i, center_j


def get_centroid(obj):
    return get_centroid_from_coords(obj.coords)


def get_mirror_axis(obj0, obj1):
    """get the axis to mirror obj0 with given obj1
    """
    obj1_centroid = get_centroid(obj1)
    edge = obj0.has_edge(obj1)
    if edge == "vertical" or edge == "both":
        return (obj1_centroid[0], None)
    else:
        return (None, obj1_centroid[1])


if 0:
    # TODO

    def get_point_from_relative_pos(filtered_point, relative_point, relative_pos: RelativePosition):
        """
        get the point to insert new node given
        filtered_point: the centroid of the filtered node
        relative_point: the centroid of the target node, or static point such as (0,0)
        relative_pos: the relative position of the filtered_point to the relative_point
        """
        if relative_pos == RelativePosition.SOURCE:
            return filtered_point
        elif relative_pos == RelativePosition.TARGET:
            return relative_point
        elif relative_pos == RelativePosition.MIDDLE:
            y = (filtered_point[0] + relative_point[0]) // 2
            x = (filtered_point[1] + relative_point[1]) // 2
            return (y, x)


def bind_parameters(index, ga, pbi, ti_param_name):
    VERBOSE = False
    assert isinstance(pbi, ParamBindingInstruction)
    pb = ParameterBinding(ga)
    func = getattr(pb, pbi.name)
    target_index = func(index, **pbi.params)

    msg = f"target_index is None for {ti_param_name} - why would this ever happen?"
    assert target_index is not None, msg

    if VERBOSE:
        print(ga.original_grid)
        print(f"{pbi} --> {ti_param_name}({target_index})")

    # retrieve value, ex. colour of the neighbor with size 1
    if ti_param_name in ("colour", "line_colour"):
        obj = ga.get_obj(target_index)
        target_colour = obj.colour
        return target_colour

    elif ti_param_name == "direction":
        target_direction = get_relative_pos(ga, index, target_index)
        if VERBOSE:
            print("target_direction = get_relative_pos(index, target_index)")
            print(f"{target_direction} = get_relative_pos({index}, {target_index}")
        return target_direction

    elif ti_param_name == "mirror_axis":
        obj0 = ga.get_obj(index)
        obj1 = ga.get_obj(target_index)
        target_axis = get_mirror_axis(obj0, obj1)
        return target_axis

    elif ti_param_name == "point":
        target_point = get_centroid(target_index)
        return target_point

    else:
        raise ValueError("unsupported dynamic parameter")

