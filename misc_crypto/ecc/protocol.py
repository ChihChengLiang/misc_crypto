from typing import Protocol, Union

IntOrFE = Union[int, "FieldElement"]


class FieldElement(Protocol):
    def __add__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __mul__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __sub__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __div__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __rmul__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __radd__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __rsub__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __pow__(self, other: int) -> "FieldElement":
        ...

    def __neg__(self) -> "FieldElement":
        ...

    @classmethod
    def one(cls) -> "FieldElement":
        ...

    @classmethod
    def zero(cls) -> "FieldElement":
        ...
