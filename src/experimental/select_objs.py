" Filters are used to select nodes (objects) from the graph "

class HasA:
    pass


class IsA:
    def is_a_rectangle(self):
        pass

    def is_a_square(self):
        pass

    def is_a_horizontal_line(self):
        pass

    def is_a_vertical_line(self):
        pass


class Selector:

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

        if number == "lots":
            return count > 2
        else:
            assert 0 <= number <= 2
            return count == number

    def select_all(self):
        return list(self.ga.objs)

    def select_one(self, where=None):
        return list(self.ga.objs)

    def all_by(self, list_of_isa, list_of_hasa):
        """
        return true if node has given colour.
        if exclude, return true if node does not have given colour.
        """
        obj = self.ga.get_obj(index)

        result = []
        if self.ga.is_multicolour:
            for obj in self.ga.objs:
                if colour in obj.colours:
                    result.append(obj)
        else:
            for obj in self.ga.objs:
                if obj.colour == colour:
                    result.append(obj)

        return result

    def inverse(self, colour: int):
