from mcarga.core.baseenum import BaseEnum, auto

class State:
    """ the state is attached to each node.  This includes:
       - the original arc task
       - the entire Program up to this node

       - the abstraction used to generate graph
       - original train input graphs / train output graphs
       - original test input graphs
    """

    def __init__(self, arc_task, abstraction, program):
        self.arc_task = arc_task

        # list of instructions
        self.program = program.copy()

        self.abstraction = abstraction
        self.train_input_graphs = abstraction.get_trains_inputs(arc_task)
        self.train_output_graphs = abstraction.get_trains_outputs(arc_task)
        self.test_input_graphs = abstraction.get_test_inputs(arc_task)

        self.simulation_statistics = []

    def copy(self):
        State(self.arc_task, self.abstraction, self.program)

    def apply_program(self, train_graphs=True, test_graphs=True):
        assert train_graphs or test_graphs
        if train_graphs:
            for g in self.train_input_graphs:
                yield self.program.apply(g)

        if test_graphs:
            for g in self.test_graphs:
                yield self.program.apply(g)

    def is_terminal(self):
        #XXX dont do this, used score
        for in_g, out_g in zip(state.apply_program(train_graphs=True), self.train_output_graphs):
            if in_g.undo_abstraction() != out_g.undo_abstraction():
                return False
        return True


class Task:
    def __init__(self, name, is_primitive):
        self.name = name
        self.is_primitive = is_primitive

    def execute(self, state, instruction):
        # Create a new state and add instruction
        state = state.copy()
        state.add_instruction(instruction)

        # create a new node
        if self.is_primitive:
            state.is_terminal()

            new_node = MCTSNode(state, self, score)
        self.children.append(new_node)


    def decompose(self):
        # For composite tasks, return subtasks
        if not self.primitive:
            return self.subtasks
        return []


class SearchTreeNode:
    def __init__(self):
        pass


class CompositeTask:
    def decompose(self, state):
        yield subtask

class PrimitiveTask:
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Execute the task and return the new state
        pass



class SearchTreeNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []

        self.todo_insturctions = []

        self.visits = 0
        self.best_score = 0
        self.task = None  # Can be a CompositeTask or PrimitiveTask

class CompositeTask:
    def decompose(self, state: Dict[str, Any]) -> List['Task']:
        # Return a list of subtasks (Composite or Primitive)
        pass

class PrimitiveTask:
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Execute the task and return the new state
        pass
