" Filters are used to select nodes (objects) from the graph "

from itertools import combinations

from mcarga.core.alogger import log

from mcarga.instruction import FilterInstruction, FilterInstructions
from mcarga.gen_values import PossibleValuesFilters

from mcarga.selection import config


class Filters:
    " filters take the form of filter(index, **params), return true if node satisfies filter "

    def __init__(self, ga):
        self.ga = ga

    def has_similar_shapes(self, index, number):
        '''
              number == 0 - > this is unique
              number == 1 - > this and another are both similar
              number == 2 - > 3 shapes similar
              number == lots - > more than 3
        '''

        obj = self.ga.get_obj(index)

        count = 0
        for other in self.ga.objs:
            if obj is other:
                continue

            if other.get_signature_shape() == obj.get_signature_shape():
                count += 1

            # no point counting anymore
            if count > 2:
                break

        if number == "many":
            return count > 2
        else:
            assert 0 <= number <= 2
            return count == number

    def select_all(self, index):
        return True

    def by_colour(self, index, colour: int, exclude: bool = False):
        """
        return true if node has given colour.
        if exclude, return true if node does not have given colour.
        """
        if colour == "most":
            colour = self.ga.most_common_colour

        elif colour == "least":
            colour = self.ga.least_common_colour

        obj = self.ga.get_obj(index)

        if self.ga.is_multicolour:
            result = colour in obj.colours
        else:
            result = obj.colour == colour

        if exclude:
            result = not result

        return result

    def by_size(self, index, size, exclude: bool = False):
        """
        return true if node has size equal to given size.
        if exclude, return true if node does not have size equal to given size.
        """

        if size == "minmax":
            max_size = max(obj.size for obj in self.ga.objs)
            min_size = min(obj.size for obj in self.ga.objs)
            obj = self.ga.get_obj(index)
            if obj.size in (min_size, max_size):
                return not exclude

        if size == "max":
            size = max(obj.size for obj in self.ga.objs)

        elif size == "2nd":
            # Step 1: Find the maximum size
            max_size = max(obj.size for obj in self.ga.objs)

            # Step 2: Find the second largest size
            intermediate = [obj.size for obj in self.ga.objs if obj.size < max_size]
            if intermediate:
                size = max(intermediate)
            else:
                size = -1

        elif size == "3rd":
            # Step 1: Find the maximum size
            size = max(obj.size for obj in self.ga.objs)

            for i in range(2):
                # Step 2: Find the second largest size
                intermediate = [obj.size for obj in self.ga.objs if obj.size < size]
                if intermediate:
                    size = max(intermediate)
                else:
                    size = -1
                    break

        elif size == "min":
            size = min(obj.size for obj in self.ga.objs)

        obj = self.ga.get_obj(index)
        if size == "odd":
            result = obj.size % 2 != 0
        else:
            result = obj.size == size

        if exclude:
            result = not result
        return result

    def by_neighbour_size(self, index, size):
        """
        return true if node has a neighbour of a given size.
        """
        if size == "max":
            obj = max(self.ga.objs, key=lambda o: o.size)
            size = obj.size

        elif size == "min":
            obj = min(self.ga.objs, key=lambda o: o.size)
            size = obj.size

        obj = self.ga.get_obj(index)

        for neighbour in obj.neighbours():
            if size == "odd":
                if neighbour.size % 2 != 0:
                    return True
            else:
                if neighbour.size == size:
                    return True
        return False

    def by_neighbour_colour(self, index, colour):
        """
        return true if node has a neighbour of a given colour.
        """
        obj = self.ga.get_obj(index)

        if colour == "same":
            # XXX going to break with ArcMultiObject
            colour = obj.colour
        elif colour == "most":
            colour = self.ga.most_common_colour
        elif colour == "least":
            colour = self.ga.least_common_colour

        for neighbour in obj.neighbours():
            if neighbour.colour == colour:
                return True
        return False


def apply_filters(filter_instructions: FilterInstructions, ga, index):
    """ with a graph and arc object index, return True if node satisfies all filters in this
    instruction
    """
    the_filterer = Filters(ga)
    for fi in filter_instructions:
        func = getattr(the_filterer, fi.name)
        if not func(index, **fi.params):
            return False
    return True


def gather_filtered_objects(filter_instructions: FilterInstructions,
                            input_graphs_bundle):
    ''' applies the filters to each object in each graph in the bundle. '''

    ONLY_ALL_GRAPHS = False
    ONLY_ALL_TEST_GRAPHS = True

    filtered_indices = []
    missed_count = 0
    missed_test_count = 0
    for i, ga in enumerate(input_graphs_bundle):

        filtered_indices_by_graph = []
        for index in ga.indices():
            if apply_filters(filter_instructions, ga, index):
                filtered_indices_by_graph.append((i, index))

        # if the filter result is the empty set for *all* graph - in this case returns None
        if not filtered_indices_by_graph:
            missed_count += 1
            if not ga.is_training_graph:
                missed_test_count += 1

        filtered_indices.extend(filtered_indices_by_graph)

    if missed_count == len(input_graphs_bundle):
        return None

    if ONLY_ALL_GRAPHS and missed_count:
        return None

    if ONLY_ALL_TEST_GRAPHS and missed_test_count:
        return None

    return frozenset(filtered_indices)


def get_candidate_filters(input_graphs_bundle, do_combined_filters=False):
    """
    return list of candidate filters.  combine is a simple AND.
    """

    VERBOSE = False

    IGNORE_DUPLICATES = True
    IGNORE_DUPLICATES_EXCLUDES = True

    IGNORE_DOUBLE_SAME_FILTERS = True

    # list of FilterInstructions
    result_filter_instructions = []

    # use this list to avoid filters that return the same set of nodes
    filtered_objs_all = set()

    mapping = {}

    for filter_op in config.filter_ops:
        # first, we generate all possible values for each parameter
        filter_op = filter_op.replace("filter_", "")
        func = getattr(Filters, filter_op)
        pv = PossibleValuesFilters(func, input_graphs_bundle)

        # then, we combine all generated values to get all possible combinations of parameters
        # do excludes afterwards
        all_candidate_filters = []
        all_candidate_filters_excluded = []

        for param_vals in pv.product_of():
            candidate_fi = FilterInstruction(filter_op, param_vals)

            if "exclude" in param_vals and param_vals["exclude"]:
                all_candidate_filters_excluded.append(candidate_fi)
            else:
                all_candidate_filters.append(candidate_fi)

        for candidate_fi in all_candidate_filters:
            filtered_objs = gather_filtered_objects([candidate_fi], input_graphs_bundle)

            # we didn't produce a filtered node for at least one graph
            if filtered_objs is None:
                continue

            # check if is duplicate
            if IGNORE_DUPLICATES and filtered_objs in filtered_objs_all:
                continue

            filtered_instructions = FilterInstructions(candidate_fi)
            mapping[filtered_instructions] = filtered_objs
            filtered_objs_all.add(filtered_objs)
            result_filter_instructions.append(filtered_instructions)

        for candidate_fi in all_candidate_filters_excluded:
            filtered_objs = gather_filtered_objects([candidate_fi], input_graphs_bundle)

            # we didn't produce a filtered node for at least one graph
            if filtered_objs is None:
                continue

            # check if is duplicate
            if IGNORE_DUPLICATES_EXCLUDES and filtered_objs in filtered_objs_all:
                continue

            filtered_instructions = FilterInstructions(candidate_fi)
            mapping[filtered_instructions] = filtered_objs
            filtered_objs_all.add(filtered_objs)
            result_filter_instructions.append(filtered_instructions)

    log(f"Found {len(result_filter_instructions)} applicable filters before combos")

    if VERBOSE:
        for ii, (instruction, indices) in zip(range(20), mapping.items()):
            print(f"{ii} : {instruction} -> {indices}")

    if not do_combined_filters:
        return result_filter_instructions

    combined_filter_instructions = [(f1, f2) for f1, f2 in combinations(result_filter_instructions, 2)]

    for candidate_fi0, candidate_fi1 in combined_filter_instructions:
        if IGNORE_DOUBLE_SAME_FILTERS:
            assert len(candidate_fi0.list_of_fi) == 1
            assert len(candidate_fi1.list_of_fi) == 1

            # underhand illegal fishing
            if candidate_fi0.list_of_fi[0].name == candidate_fi1.list_of_fi[0].name:
                continue

        combined_fis = FilterInstructions(candidate_fi0, candidate_fi1)
        filtered_objs = gather_filtered_objects(combined_fis, input_graphs_bundle)

        # we didn't produce a filtered node for at least one graph
        if filtered_objs is None:
            continue

        # check if is duplicate
        if IGNORE_DUPLICATES and filtered_objs in filtered_objs_all:
            continue

        mapping[combined_fis] = filtered_objs
        filtered_objs_all.add(filtered_objs)
        result_filter_instructions.append(combined_fis)

    log(f"Found {len(result_filter_instructions)} applicable filters (after combos)")

    if VERBOSE:
        for ii, (instruction, indices) in zip(range(42), mapping.items()):
            print(f"{ii} : {instruction} -> {indices}")

    # XXX idea: reorder based on the number of filtered nodes
    return result_filter_instructions
