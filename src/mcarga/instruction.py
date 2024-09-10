from mcarga.gen_values import ParamBindingArg


class FilterInstruction:
    ''' filters are applied to all objects in graph, and return a subset of objects '''
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def __repr__(self):
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}(index, {params_str})"


class FilterInstructions:
    ''' 1 or more filters that all need to be satisfied per object '''
    def __init__(self, *filter_instructions):
        self.list_of_fi = []
        for fi in filter_instructions:
            if isinstance(fi, FilterInstruction):
                self.list_of_fi.append(fi)
            else:
                assert isinstance(fi, FilterInstructions)
                self.list_of_fi += fi.list_of_fi

    def __iter__(self):
        return iter(self.list_of_fi)

    def __len__(self):
        return len(self.list_of_fi)

    def __repr__(self):
        return f"filters: {self.list_of_fi}"


class ParamBindingInstruction:
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def __repr__(self):
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}({params_str})"


class TransformationInstruction:
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def has_param_binding(self):
        for p in self.params.values():
            if isinstance(p, ParamBindingArg):
                return True

        return False

    def __repr__(self):
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}(index, {params_str})"


class Instruction:
    def __init__(self, fis, ti, pbi=None):
        self.fis = fis
        self.ti = ti
        if pbi is not None:
            assert isinstance(pbi, ParamBindingInstruction)
        self.param_binding_instruction = pbi

    def is_param_binding_set(self):
        return self.param_binding_instruction is not None

    def __repr__(self):
        s = f"INSTR - {self.fis} "
        if self.is_param_binding_set():
            s += f"[[{self.param_binding_instruction}]] "
        s += f"---> transformation: {self.ti}"
        return s
