from mcarga.statemachine.graph_abstraction import ArcObject

from mcarga.abstractions.factory import GraphBundle
from mcarga.gen_values import PossibleValuesTransformations
from mcarga.instruction import TransformationInstruction

from mcarga.core.definitions import Direction, Rotation, Mirror, RelativePosition, RelativeTo, SplitDirection


class Transformations:
    def __init__(self, ga, local_blackboard=None):
        self.ga = ga
        self.local_blackboard = local_blackboard

    def change_background_colour(self, index, colour):
        self.ga.set_background_colour(colour)

    def update_colour(self, index, colour):
        """
        update obj colour to given colour
        """

        obj = self.ga.get_obj(index)
        assert isinstance(obj, ArcObject)

        if colour == "blackboard":
            mapping = self.local_blackboard.simple_colour_mapping()
            if not mapping:
                return False
            if obj.colour not in mapping:
                return False
            colour = mapping[obj.colour]

        elif colour == "most":
            colour = self.ga.most_common_colour

        elif colour == "least":
            colour = self.ga.least_common_colour

        if obj.colour == colour:
            return False

        obj.colour = colour
        obj.update()
        return True

    def split_object(self, index, split_direction: SplitDirection):
        """
        """
        obj = self.ga.get_obj(index)
        assert isinstance(obj, ArcObject)

        i, j, height, width = obj.bounding_box()

        new_objs = []
        if split_direction == SplitDirection.VERTICAL:
            mid_height = i + height / 2
            below, above = [], []
            for i, j in obj.coords:
                if i < mid_height:
                    below.append((i, j))
                else:
                    above.append((i, j))
            if below:
                new_objs.append(below)
            if above:
                new_objs.append(above)
        else:
            assert split_direction == SplitDirection.HORIZONTAL
            mid_width = j + width / 2
            left, right = [], []
            for i, j in obj.coords:
                if j < mid_width:
                    left.append((i, j))
                else:
                    right.append((i, j))
            if left:
                new_objs.append(left)
            if right:
                new_objs.append(right)

        for cc in new_objs:
            self.ga.create_single_obj(cc, obj.colour)

        self.ga.remove_object(index)
        return True

    def move_object(self, index, direction: Direction):
        """
        move object by 1 pixel in a given direction
        # XXX allow collisions and/or escaping from edge of grid?
        """
        assert direction is not None

        delta_row, delta_col = Direction.deltas(direction)

        obj = self.ga.get_obj(index)
        updated_coords = [(row + delta_row, col + delta_col) for row, col in obj.coords]
        obj.coords = updated_coords
        obj.update()
        return True

    def move_object_max(self, index, direction: Direction):
        """
        move obj in a given direction until it hits another obj or the edge of the image
        """
        assert direction is not None

        obj = self.ga.get_obj(index)

        delta_i, delta_j = Direction.deltas(direction)

        max_allowed = 30
        for foo in range(max_allowed):
            updated_coords = [(i + delta_i, j + delta_j) for i, j in obj.coords]

            # stop extending obj until hitting edge of grid
            if not self.ga.check_within_grid(*updated_coords):
                break

            # if overlap not allowed, stop extending obj until hitting edge of image or another obj
            if self.ga.check_collision(obj, *updated_coords):
                break

            obj.coords = updated_coords
            obj.update()
        return True

    def extend_object(self, index, direction: Direction, overlap: bool = False):
        """
        extend obj in a given direction,
        if overlap is true, extend obj even if it overlaps with another obj
        if overlap is false, stop extending before it overlaps with another obj
        """
        assert direction is not None

        delta_row, delta_col = Direction.deltas(direction)

        obj = self.ga.get_obj(index)
        updated_coords = obj.coords[:]
        for row_i, col_j in obj.coords:
            max_allowed = 30
            for foo in range(max_allowed):
                row_i += delta_row
                col_j += delta_col

                # stop extending obj until hitting edge of grid
                if not self.ga.check_within_grid((row_i, col_j)):
                    break

                # if overlap not allowed, stop extending obj until hitting edge of image or another obj
                if not overlap and self.ga.check_collision(obj, (row_i, col_j)):
                    break

                updated_coords.append((row_i, col_j))

        obj.coords = updated_coords
        obj.update()
        return True

    def rotate_object(self, index, rotation_dir: Rotation):
        """
        rotates obj around its center point in a given rotational direction
        """
        rotate_times = 1
        if rotation_dir == Rotation.CW:
            mul = -1
        elif rotation_dir == Rotation.CCW:
            mul = 1
        elif rotation_dir == Rotation.CW2:
            rotate_times = 2
            mul = -1

        # Calculate true center of mass
        obj = self.ga.get_obj(index)
        center_i = sum(i for i, _ in obj.coords) / len(obj.coords)
        center_j = sum(j for _, j in obj.coords) / len(obj.coords)

        for t in range(rotate_times):
            updated_coords = []
            if isinstance(obj, ArcObject):
                for i, j in obj.coords:
                    # Translate to origin
                    i, j = (i - center_i, j - center_j)

                    # Rotate
                    i, j = (-j * mul, i * mul)

                    # Translate back
                    i, j = (i + center_i, j + center_j)

                    # Round to nearest integer
                    i, j = int(round(i)), int(round(j))
                    updated_coords.append((i, j))

                obj.coords = updated_coords
                obj.update()
            else:
                for c, (i, j) in obj.colour_coords:
                    # Translate to origin
                    i, j = (i - center_i, j - center_j)

                    # Rotate
                    i, j = (-j * mul, i * mul)

                    # Translate back
                    i, j = (i + center_i, j + center_j)

                    # Round to nearest integer
                    i, j = int(round(i)), int(round(j))
                    updated_coords.append((c, (i, j)))

                obj.colour_coords = updated_coords
                obj.update()
        return True

    def mirror_object(self, index, mirror_direction: Mirror):
        """
        Mirrors the given object in the specified direction: horizontal, vertical, diagonal left/right
        """
        obj = self.ga.get_obj(index)
        coords = obj.coords

        new_coords = []

        def adjust_coords(ij_func):
            if isinstance(obj, ArcObject):
                return [ij_func(i, j) for i, j in obj.coords]
            else:
                return [(c, ij_func(i, j)) for c, (i, j) in obj.colour_coords]

        if mirror_direction == Mirror.VERTICAL:
            max_i = max(i for i, j in coords)
            min_i = min(i for i, j in coords)

            def next_ij(ii, jj):
                return (max_i - (ii - min_i), jj)

            new_coords = adjust_coords(next_ij)

        elif mirror_direction == Mirror.HORIZONTAL:
            max_j = max(j for i, j in coords)
            min_j = min(j for i, j in coords)

            def next_ij(ii, jj):
                return (ii, max_j - (jj - min_j))

            new_coords = adjust_coords(next_ij)

        elif mirror_direction == Mirror.DIAGONAL_LEFT:  # \
            min_i = min(i for i, j in coords)
            min_j = min(j for i, j in coords)

            def next_ij(ii, jj):
                return jj - min_j + min_i, ii - min_i + min_j

            new_coords = adjust_coords(next_ij)

        elif mirror_direction == Mirror.DIAGONAL_RIGHT:  # /
            min_i = min(i for i, j in coords)
            max_j = max(j for i, j in coords)

            def next_ij(ii, jj):
                return max_j - jj + min_i, min_i - ii + max_j

            new_coords = adjust_coords(next_ij)
        else:
            raise ValueError("Invalid mirror direction")

        if isinstance(obj, ArcObject):
            if not self.ga.check_collision(obj, *new_coords):
                obj.coords = new_coords
                obj.update()
        else:
            if not self.ga.check_collision(obj, *[c for _, c in new_coords]):
                obj.colour_coords = new_coords
                obj.update()
        return True

    def reflect_axis(self, index, mirror_axis):
        """
        reflects an object with respect to the given axis.
        mirror_axis takes the form of (i, j) where one of i, j equals None to
        indicate the other being the axis of mirroring
        """
        obj = self.ga.get_obj(index)
        coords = obj.coords
        new_coords = []

        axis_i, axis_j = mirror_axis

        if axis_j is None:
            assert axis_i is not None

            # Mirror horizontally
            for i, j in coords:
                new_i = 2 * axis_i - i
                new_coords.append((new_i, j))

        elif axis_i is None:
            assert axis_j is not None

            # Mirror vertically
            for i, j in coords:
                new_j = 2 * axis_j - j
                new_coords.append((i, new_j))
        else:
            raise ValueError("Invalid mirror axis. One of i or j must be None.")

        if not self.ga.check_collision(obj, *new_coords):
            obj.coords = new_coords
            obj.update()
            return True
        else:
            # print(f"Warning: Reflex axis transformation for obj {obj} resulted in a collision. Operation aborted.")
            return False

    def add_border_around_object(self, index, border_colour):
        """
        Adds a border with thickness 1 and border_colour around the given object.
        XXX does insides.  overall bit simplistic
        """
        obj = self.ga.get_obj(index)
        coords = obj.coords

        border_coords = set()
        for i, j in coords:
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    border_coord = (i + di, j + dj)
                    if not self.ga.check_pixel_occupied(border_coord):
                        border_coords.add(border_coord)

        border_coords = list(border_coords)

        if border_coords:
            self.ga.create_single_obj(border_coords, border_colour)
            return True
        return False

    def hollow_rectangle(self, index, fill_colour):
        """
        Hollows out the rectangle containing the given object, filling the interior with the specified colour.
        """

        obj = self.ga.get_obj(index)
        coords = obj.coords

        # Find the bounding box
        min_i = min(i for i, _ in coords)
        max_i = max(i for i, _ in coords)
        min_j = min(j for _, j in coords)
        max_j = max(j for _, j in coords)

        # Separate border and interior coordinates
        border_coords = []
        interior_coords = []
        for i, j in coords:
            if i in (min_i, max_i) or j in (min_j, max_j):
                border_coords.append((i, j))
            else:
                interior_coords.append((i, j))

        # Update the original object to be just the border
        obj.coords = border_coords
        obj.update()

        # Create a new object for the interior if it's not the background colour
        if not interior_coords:
            return False

        if self.ga.is_multicolour:
            self.ga.create_multi_obj([(fill_colour, c) for c in interior_coords])
        else:
            self.ga.create_single_obj(interior_coords, fill_colour)
        return True

    def fill_rectangle(self, index, fill_colour, overlap: bool):
        """
        fill the rectangle containing the given obj with the given colour.
        if overlap is True, fill the rectangle even if it overlaps with other nodes.
        """
        obj = self.ga.get_obj(index)

        if fill_colour == "same":
            fill_colour = obj.colour

        min_i = min(i for i, _ in obj.coords)
        max_i = max(i for i, _ in obj.coords)
        min_j = min(j for _, j in obj.coords)
        max_j = max(j for _, j in obj.coords)

        unfilled_coords = []
        for i in range(min_i, max_i + 1):
            for j in range(min_j, max_j + 1):
                coord = (i, j)
                if coord not in obj.coords:
                    if overlap:
                        unfilled_coords.append(coord)
                    elif not self.ga.check_pixel_occupied(coord):
                        unfilled_coords.append(coord)

        if not unfilled_coords:
            return False

        # XXX this isn't exactly valid, since unfilled_coords might not be connected
        if self.ga.is_multicolour:
            self.ga.create_multi_obj([(fill_colour, c) for c in unfilled_coords])
        else:
            self.ga.create_single_obj(unfilled_coords, fill_colour)
        return True

    def remove_object(self, index):
        """
        remove a obj from the graph
        """
        self.ga.remove_object(index)
        return True

    def insert(self, node, object_id, point, relative_pos: RelativePosition):
        """
        insert some pattern identified by object_id at some location,
        the location is defined as, the relative position between the given node and point.
        for example, point=top, relative_pos=middle will insert the pattern between the given node
        and the top of the ga.
        if object_id is -1, use the pattern given by node
        """

        node_centroid = self.get_centroid(node)
        if not isinstance(point, tuple):
            if point == RelativeTo.TOP:
                point = (0, node_centroid[1])
            elif point == RelativeTo.BOTTOM:
                point = (self.ga.height - 1, node_centroid[1])
            elif point == RelativeTo.LEFT:
                point = (node_centroid[0], 0)
            elif point == RelativeTo.RIGHT:
                point = (node_centroid[0], self.ga.width - 1)
            elif point == RelativeTo.TOP_LEFT:
                point = (0, 0)
            elif point == RelativeTo.TOP_RIGHT:
                point = (0, self.ga.width - 1)
            elif point == RelativeTo.BOTTOM_LEFT:
                point = (self.ga.height - 1, 0)
            elif point == RelativeTo.BOTTOM_RIGHT:
                point = (self.ga.height - 1, self.ga.width - 1)
        if object_id == -1:

            # special id for dynamic objects, which uses the given nodes as objects
            object = self.graph.nodes[node]
        else:
            object = self.ga.task.static_objects_for_insertion[self.abstraction][object_id]
        target_point = self.get_point_from_relative_pos(node_centroid, point, relative_pos)
        object_centroid = self.get_centroid_from_pixels(object["coords"])
        subnodes_coords = []
        for subnode in object["coords"]:
            delta_y = subnode[0] - object_centroid[0]
            delta_x = subnode[1] - object_centroid[1]
            subnodes_coords.append((target_point[0] + delta_y, target_point[1] + delta_x))
        new_node_id = self.generate_node_id(object["colour"])
        self.graph.add_node(new_node_id, nodes=list(subnodes_coords), colour=object["colour"],
                            size=len(list(subnodes_coords)))
        return self

    def draw_line(self, index, start_position: RelativeTo, direction: Direction, line_colour):
        """
        """

        # we need a to coord to start
        obj = self.ga.get_obj(index)
        i, j, height, width = obj.bounding_box()
        if start_position == RelativeTo.TOP_LEFT:
            i -= 1
            j -= 1
        elif start_position == RelativeTo.TOP_RIGHT:
            i -= 1
            j += width
        elif start_position == RelativeTo.TOP:
            i -= 1
            j += width // 2
        elif start_position == RelativeTo.LEFT:
            i += height // 2
            j -= 1
        elif start_position == RelativeTo.RIGHT:
            i += height // 2
            j += width
        elif start_position == RelativeTo.BOTTOM:
            i += height
            j += width // 2
        elif start_position == RelativeTo.BOTTOM_LEFT:
            i += height
            j -= 1
        elif start_position == RelativeTo.BOTTOM_RIGHT:
            i += height
            j += width

        line_coords = []

        delta_row, delta_col = Direction.deltas(direction)
        while True:
            line_coords.append((i, j))
            i += delta_row
            j += delta_col

            # stop extending if hit edge of grid
            if not self.ga.check_within_grid((i, j)):
                break

        if not line_coords:
            return False

        if line_colour == "self":
            line_colour = obj.colour

        self.ga.create_single_obj(line_coords, line_colour)
        return True

    def draw_line_from_point(self, index, direction: Direction, line_colour):
        """
        index - needs to be of size 1.  This needs to be fed to filters.
        """

        # we need a to coord to start
        obj = self.ga.get_obj(index)

        if obj.size != 1:
            return False

        line_coords = []

        delta_row, delta_col = Direction.deltas(direction)
        i, j = obj.coords[0]
        while True:
            i += delta_row
            j += delta_col

            coord = (i, j)

            # stop growing line if hit edge of grid
            if not self.ga.check_within_grid(coord):
                break

            if self.ga.check_pixel_occupied(coord):
                break

            line_coords.append(coord)

        if not line_coords:
            return False

        if line_colour == "self":
            line_colour = obj.colour

        self.ga.create_single_obj(line_coords, line_colour)
        return True


def generate_params_for_transformation(transformation_name: str,
                                       input_bundle: GraphBundle):

    """ generate all the params for transformation

    literally generates TransformationInstruction """

    func = getattr(Transformations, transformation_name)
    pv = PossibleValuesTransformations(func, input_bundle)

    for param_vals in pv.product_of():
        yield TransformationInstruction(transformation_name, param_vals)


def get_all_transformations(transformations, input_bundle):
    """
    generate candidate transformations, return list of full operations candidates
    """
    for transformation_name in transformations:
        for ti in generate_params_for_transformation(transformation_name, input_bundle):
            yield ti


