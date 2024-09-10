from inspect import signature
from itertools import product

from mcarga.core.baseenum import BaseEnum
from mcarga.core.definitions import RelativeTo


class PossibleValuesBase:
    skip_parameters_names = ["self", "index"]

    def __init__(self, function, input_bundle):
        self.function_signature = signature(function)
        self.input_bundle = input_bundle

    def gen_all_possible(self):
        " returns all possible values as a list of lists "

        name_mapping = {}
        type_mapping = {}

        def add_to_map(prefix, mapping):
            if name.startswith(prefix):
                func = getattr(self, name)
                assert callable(func)

                extracted_name = name.replace(prefix, "")
                mapping[extracted_name] = func

        for name in dir(self):
            add_to_map('gen_name__', name_mapping)
            add_to_map('gen_type__', type_mapping)

        sig = self.function_signature

        for param in sig.parameters:
            param_name = sig.parameters[param].name
            param_type = sig.parameters[param].annotation
            param_type_name = param_type.__name__

            if param_name in self.skip_parameters_names:
                continue

            if param_name in name_mapping:
                possible_values = name_mapping[param_name]()

            elif issubclass(param_type, BaseEnum):
                # uggh.... XXX hack hack
                possible_values = type_mapping["enum"](param_type)

            elif param_type_name in type_mapping:
                possible_values = type_mapping[param_type_name](param_type)

            else:
                possible_values = []

            # generic method to override
            possible_values += self.extend_possible_values(param_name, possible_values)

            if not possible_values:
                assert False, f"Unsupported parameter {param_name}"

            yield param_name, possible_values

    def extend_possible_values(self, param_name, possible_values):
        return []

    def product_of(self):
        # need just the values for product
        param_names = [name for name, values in self.gen_all_possible()]
        possible_values = [values for name, values in self.gen_all_possible()]
        for combo in product(*possible_values):
            # generate dictionary, keys are the parameter names, values are the corresponding values
            yield {name: values for name, values in zip(param_names, combo)}


class PossibleValuesFilters(PossibleValuesBase):
    def gen_name__colour(self):
        all_colours = set()
        for ga in self.input_bundle:
            all_colours.update(ga.all_colours_for_filters())
        return [c for c in sorted(all_colours)] + ["most", "least"]

    def gen_name__size(self):
        object_sizes = self.input_bundle.static_object_attributes(lambda o: o.size)
        return  [w for w in object_sizes] + ["min", "max", "minmax", "2nd", "3rd", "odd"]

    def gen_type__bool(self, typ):
        return [False, True]

    def gen_type__enum(self, typ):
        return [value for value in typ]


class ParamBindingArg:
    " prolog style we will bind later "
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.name.upper()}?"


class PossibleValuesTransformations(PossibleValuesBase):
    # "mirror_direction" <- i dont this this makes sense ever
    # TODO "point" for insertion

    dynamic_param_binding = ["colour", "line_colour", "direction", "mirror_axis"]

    def gen_name__colour(self):
        bg_colour = None
        for ga in self.input_bundle:
            if bg_colour is None:
                bg_colour = ga.background_colour
            else:
                if bg_colour != ga.background_colour:
                    bg_colour = None
                    break

        return ["most", "least"] + [c for c in range(10) if c != bg_colour]

    def gen_name__fill_colour(self):
        return [c for c in range(10)]

    def gen_name__border_colour(self):
        return [c for c in range(10)]

    def gen_name__line_colour(self):
        return self.gen_name__colour() + ["self"]

    def gen_name__object_id(self):
        # XXX TODO
        static_objs = self.blackboard.static_objs
        return [id for id in range(len(static_objs))] + [-1]

    def gen_name__point(self):
        # for insertion, could be RelativeTo or a coordinate on image (tuple)
        return [value for value in RelativeTo]

    def gen_type__bool(self, typ):
        return [True, False]

    def gen_type__enum(self, typ):
        return [value for value in typ]

    def extend_possible_values(self, param_name, possible_values):
        if param_name in self.dynamic_param_binding:
            return [ParamBindingArg(param_name)]
        return []


class PossibleValuesDynamicParams(PossibleValuesBase):
    def gen_name__colour(self):
        all_colours = set()
        for ga in self.input_bundle:
            all_colours.update(ga.all_colours)
        return [c for c in sorted(all_colours)] + ["most", "least"]

    def gen_name__size(self):
        object_sizes = self.input_bundle.static_object_attributes(lambda o: o.size)
        return [w for w in object_sizes] + ["min", "max", "2nd", "3rd"]

    def gen_type__bool(self, typ):
        return [True, False]

    def gen_type__enum(self, typ):
        return [value for value in typ]

