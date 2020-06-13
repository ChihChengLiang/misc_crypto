from typing import NewType, Protocol, Union
from py_ecc.bn128 import curve_order
from py_ecc.fields import FQ

G1 = NewType("G1", int)


# All the algebra of the circuit must be in the Fr Field
class Fr(FQ):
    field_modulus = curve_order


IntOrFE = Union[int, "FieldElement"]

class Curve(Protocol):
    G1: "FieldElement"
    G2: "FieldElement"


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
