from enum import Enum, auto

class BaseEnum(Enum):
    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"
