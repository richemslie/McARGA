list_of_rules = ["color_equal", "position_equal", "size_equal"]


def color_equal(obj1_colors, obj2_colors):
    """
    checks if the two objects passed in are the same color
    the reason why we pass in a list of colors for each object instead of just 1 color:
    in future implementation there will be objects that are multi-colored
    :param obj1_colors: list of colors from object 1
    :param obj2_colors: list of colors from object 2
    """
    return obj1_colors == obj2_colors


def position_equal(obj1_pixels, obj2_pixels):
    """
    checks if two objects have the same position
    :param obj1_pixels: list of pixel coordinates from object 1 (unsorted)
    :param obj2_pixels: list of pixel coordinates from object 2 (unsorted)
    :return:
    """
    return obj1_pixels == obj2_pixels


def size_equal(obj1_size, obj2_size):
    """
    checks if the two objects have the same size
    :param obj1_size: size of obj1
    :param obj2_size: size of obj2
    """
    return obj1_size == obj2_size


def do_constraints_local():
    for apply_filters_call in apply_filters_calls:
        constraints = constraints_acquisition_local(apply_filters_call)
        transformation_ops = prune_transformations(constraints)


def constraints_acquisition_local(apply_filter_call):
    """
    given an apply_filter_call, find the set of constraints that
    the nodes returned by the apply_filter_call must satisfy.
    these are called local constraints as they apply to only the nodes
    that satisfies the filter.
    """
    found_constraints = []
    for rule in rules.list_of_rules:
        if self.apply_constraint(rule, apply_filter_call):
            found_constraints.append(rule)
    return found_constraints


def apply_constraint(self, rule, apply_filter_call):
    """
    check if the given rule holds for all training instances for the given apply_filter_call
    """
    satisfied = True
    for index in range(len(self.train_input)):
        params = self.constraints_param_generation(apply_filter_call, rule, index)
        satisfied = satisfied and getattr(rules, rule)(*params)
    return satisfied


def constraints_param_generation(self, condition, rule, training_index):
    """
    given condition and rule, first generate the sequence using the condition
    then transform the sequence into the expected format for the constraint
    :param condition: {'filters': ['filter_nodes_by_color'],
      'filter_params': [{'color': 0, 'exclude': True}]}
    :param rule: "rule_name"
    :param training_index: training instance index
    """

    # find input and output nodes
    input_abs = self.input_abstracted_graphs[self.abstraction][training_index]
    output_abs = self.output_abstracted_graphs_original[self.abstraction][training_index]

    input_nodes = []
    for node in input_abs.graph.nodes():
        if input_abs.apply_filters(node, **condition):
            input_nodes.append(node)

    output_nodes = []
    for node in output_abs.graph.nodes():
        if output_abs.apply_filters(node, **condition):
            output_nodes.append(node)

    # now switch depending on rule name
    if rule == "color_equal":
        # get the colours from node, check if they are equal
        input_sequence = [input_abs.graph.nodes[node]["color"] for node in input_nodes]
        output_sequence = [output_abs.graph.nodes[node]["color"] for node in output_nodes]

        # XXX what - it doesnt work...
        input_sequence.sort()
        output_sequence.sort()
        args = [input_sequence, output_sequence]

    elif rule == "position_equal":
        input_sequence = []
        output_sequence = []
        for node in input_nodes:
            input_sequence.extend([subnode for subnode in input_abs.graph.nodes[node]["nodes"]])
        for node in output_nodes:
            output_sequence.extend([subnode for subnode in output_abs.graph.nodes[node]["nodes"]])
        input_sequence.sort()
        output_sequence.sort()
        args = [input_sequence, output_sequence]

    elif rule == "size_equal":
        input_sequence = [input_abs.graph.nodes[node]["size"] for node in input_nodes]
        output_sequence = [output_abs.graph.nodes[node]["size"] for node in output_nodes]
        input_sequence.sort()
        output_sequence.sort()
        args = [input_sequence, output_sequence]
    return args

def prune_transformations(self, constraints):
    """
    given a set of constraints that must be satisfied, return a set of transformations that do not violate them
    """
    transformations = self.transformation_ops[self.abstraction]
    for constraint in constraints:
        if constraint == "color_equal":
            pruned_transformations = ["update_color"]
        elif constraint == "position_equal":
            pruned_transformations = ["move_node", "extend_node", "move_node_max"]
        elif constraint == "size_equal":
            pruned_transformations = ["extend_node"]
        transformations = [t for t in transformations if t not in pruned_transformations]
    return transformations









if 0:

    def get_static_inserted_objects(self):
        """
        populate self.static_objects_for_insertion, which contains all static objects detected in the images.
        """
        self.static_objects_for_insertion[self.current_abstraction] = []
        existing_objects = []

        for i, output_abstracted_graph in enumerate(self.output_abstracted_graphs_original[self.current_abstraction]):
            # difference_image = self.train_output[i].copy()
            input_abstracted_nodes = self.input_abstracted_graphs_original[self.current_abstraction][i].graph.nodes()
            for abstracted_node, data in output_abstracted_graph.graph.nodes(data=True):
                if abstracted_node not in input_abstracted_nodes:
                    new_object = data.copy()
                    min_x = min([subnode[1] for subnode in new_object["nodes"]])
                    min_y = min([subnode[0] for subnode in new_object["nodes"]])
                    adjusted_subnodes = []
                    for subnode in new_object["nodes"]:
                        adjusted_subnodes.append((subnode[0] - min_y, subnode[1] - min_x))
                    adjusted_subnodes.sort()
                    if adjusted_subnodes not in existing_objects:
                        existing_objects.append(adjusted_subnodes)
                        self.static_objects_for_insertion[self.current_abstraction].append(new_object)


