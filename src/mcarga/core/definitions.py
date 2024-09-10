from mcarga.core.baseenum import BaseEnum, auto


class Direction(BaseEnum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    UP_LEFT = auto()
    UP_RIGHT = auto()
    DOWN_LEFT = auto()
    DOWN_RIGHT = auto()

    @staticmethod
    def deltas(direction):
        delta_row = 0
        delta_col = 0

        if direction in (Direction.UP, Direction.UP_LEFT, Direction.UP_RIGHT):
            delta_row = -1

        elif direction in (Direction.DOWN, Direction.DOWN_LEFT, Direction.DOWN_RIGHT):
            delta_row = 1

        if direction in (Direction.LEFT, Direction.UP_LEFT, Direction.DOWN_LEFT):
            delta_col = -1

        elif direction in (Direction.RIGHT, Direction.UP_RIGHT, Direction.DOWN_RIGHT):
            delta_col = 1

        return delta_row, delta_col


class Rotation(BaseEnum):
    CW = auto()
    CCW = auto()
    CW2 = auto()


class Mirror(BaseEnum):
    VERTICAL = auto()
    HORIZONTAL = auto()
    DIAGONAL_LEFT = auto()     # \
    DIAGONAL_RIGHT = auto()    # /


class SplitDirection(BaseEnum):
    VERTICAL = auto()
    HORIZONTAL = auto()


class RelativeTo(BaseEnum):
    TOP = auto()
    BOTTOM = auto()
    LEFT = auto()
    RIGHT = auto()
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()


class RelativePosition(BaseEnum):
    SOURCE = auto()
    TARGET = auto()
    MIDDLE = auto()


class ObjectProperty(BaseEnum):
    SYMMETRICAL = 0
    HOLLOW = 1
