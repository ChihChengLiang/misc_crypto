from typing import NewType, Protocol, Union
from py_ecc.optimized_bn128 import (
    pairing,
    multiply,
    add,
    G1,
    G2,
    FQ,
    neg,
    curve_order,
    FQ12,
    final_exponentiate,
    Z1,
)


# All the algebra of the circuit must be in the Fr Field
class Fr(FQ):
    field_modulus = curve_order


IntOrFE = Union[int, "FieldElement"]


def pairing_check(G1_left, G2_left, G1_right, G2_right) -> bool:
    final_exponentiation = final_exponentiate(
        pairing(G2_left, G1_left, final_exponentiate=False,)
        * pairing(G2_right, G1_right, final_exponentiate=False,)
    )
    return final_exponentiation == FQ12.one()


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




def roots_of_unity(order):
    a = field.FQ(5)
    p = curve_order
    return [a ** (i * (p - 1) / order) for i in range(order)]
