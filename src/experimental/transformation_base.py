class ObjectTransformationBase:

    def __init__(self, name, ga, local_blackboard=None):
        self.name = name
        self.ga = ga
        self.local_blackboard = local_blackboard

    def required_number_objs(self):
        return 1

    def transform(self, index0, *args):
        pass


class UpdateColour(ObjectTransformationBase):

    def __init__(self, ga, local_blackboard=None):
        super().__init__("update_colour", ga, local_blackboard)

    def required_number_objs(self):
        return 1

    def precondition_obj0(self, obj):
        ''' this is an extra condition that the selection process most pass before proceeding. '''
        return obj.is_unicoloured

    def transform(self, index0, colour):
        obj = self.ga.get_obj(index0)
        assert obj.is_unicoloured

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

        obj.set_colour(colour)
        obj.update()
        return True


class GridTransformationBase:

    def __init__(self, name, ga, local_blackboard=None):
        self.name = name
        self.ga = ga
        self.local_blackboard = local_blackboard

    def preconditions(self):
        # this must succeed before we can apply transformatio

    def transform(self, *args):
        ''' takes no objects '''
        pass
