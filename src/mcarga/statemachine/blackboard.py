from mcarga.core.baseenum import BaseEnum, auto

from mcarga.statemachine.graph_abstraction import ArcObject


class MatchType(BaseEnum):
    EXACT = auto()
    SAME_SHAPE_AND_POSITION = auto()
    SAME_SHAPE_AND_COLOUR = auto()
    SAME_SHAPE = auto()

    def __repr__(self):
        return f"MatchType.{self.name}"


class StaticType(BaseEnum):
    UNIQUE = auto()
    IN_INPUT = auto()


class Blackboard:
    def __init__(self, task_bundle):
        self.task_bundle = task_bundle

    def analysis(self):
        # this is mapping from ga_index -> in_obj_index -> (out_obj_index, match_type)
        self.in_obj_match_mapping = {}

        # this is mapping from ga_index -> out_obj_index -> (in_obj_index, match_type)
        self.out_obj_match_mapping = {}

        for ga_index, (in_ga, out_ga) in enumerate(self.task_bundle.pairs()):

            in_mapping = self.in_obj_match_mapping[ga_index] = {}
            out_mapping = self.out_obj_match_mapping[ga_index] = {}

            # similar objects
            for in_obj in in_ga.objs:
                in_matches = in_mapping.setdefault(in_obj.index, [])

                for out_obj in out_ga.objs:
                    out_matches = out_mapping.setdefault(out_obj.index, [])

                    for match_type in compare_two_objs(in_obj, out_obj):
                        in_matches.append((out_obj.index, match_type))
                        out_matches.append((in_obj.index, match_type))

    def get_exact_matches(self):
        exact_matches_list = []

        for indx, in_ga in enumerate(self.task_bundle.in_train_bundle):
            in_mapping = self.in_obj_match_mapping[indx]
            for obj_index, matches in in_mapping.items():
                for out_obj_index, match_type in matches:
                    if match_type == MatchType.EXACT:
                        exact_matches_list.append((indx, obj_index, out_obj_index))
                        break

        return exact_matches_list

    def get_static_object_for_insertion(self):
        results = []
        for indx, in_ga in enumerate(self.task_bundle.in_train_bundle):
            result = []
            out_mapping = self.out_obj_match_mapping[indx]

            for obj_index, matches in out_mapping.items():
                if not matches:
                    # nothing matches up, new object not in input
                    result.append((obj_index, StaticType.UNIQUE))

                else:
                    add = True
                    for _, match_type in matches:
                        if match_type in (MatchType.EXACT, MatchType.SAME_SHAPE_AND_POSITION):
                            add = False
                            break

                    if add:
                        result.append((obj_index, StaticType.IN_INPUT))

            if result:
                results.append((indx, result))
        return results


def compare_two_objs(obj_a, obj_b):
    assert isinstance(obj_a, ArcObject)
    assert isinstance(obj_b, ArcObject)

    sig_a = obj_a.get_signature_shape()
    sig_b = obj_b.get_signature_shape()

    if sig_a == sig_b:
        if obj_a.bounding_box() == obj_b.bounding_box():
            if obj_a.colour == obj_b.colour:
                yield MatchType.EXACT
            else:
                yield MatchType.SAME_SHAPE_AND_POSITION

        else:
            if obj_a.colour == obj_b.colour:
                yield MatchType.SAME_SHAPE_AND_COLOUR
            else:
                yield MatchType.SAME_SHAPE


if 0:
    def simple_colour_mapping(self):
        # given any two shapes that only differ by colour, if all the colour changes are the same
        # return a map of those colour changes

        colour_mapping = {}
        for in_ga, out_ga in self.task_bundle.pairs():

            ga_mapping = self.obj_match_mapping[in_ga]

            for in_index, matches in ga_mapping.items():
                in_obj = in_ga.get_obj(in_index)

                for out_index, match_type in matches:
                    # cannot know
                    if match_type == MatchType.EXACT:
                        return None

                    out_obj = out_ga.get_obj(out_index)
                    if match_type == MatchType.SAME_SHAPE_AND_POSITION:
                        if in_obj.colour in colour_mapping:
                            # contradiction
                            if colour_mapping[in_obj.colour] != out_obj.colour:
                                return None

                        else:
                            colour_mapping[in_obj.colour] = out_obj.colour

        return colour_mapping
