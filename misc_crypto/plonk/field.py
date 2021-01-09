from typing import Protocol, Union, Tuple
from py_ecc.optimized_bn128 import (
    pairing,
    FQ,
    curve_order,
    FQ12,
    final_exponentiate,
)


# All the algebra of the circuit must be in the Fr Field
class Fr(FQ):
    field_modulus = curve_order


IntOrFE = Union[int, "FieldElement"]


def pairing_check(G1_left, G2_left, G1_right, G2_right) -> bool:
    final_exponentiation = final_exponentiate(
        pairing(
            G2_left,
            G1_left,
            final_exponentiate=False,
        )
        * pairing(
            G2_right,
            G1_right,
            final_exponentiate=False,
        )
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


def roots_of_unity(order: int) -> Tuple[Fr, ...]:
    # TODO: Check the multiplicative subgroup must have size  2^n
    # TODO: Support fields other than Fr
    a = Fr(5)
    p = Fr.field_modulus - 1
    return tuple(a ** ((i * p) // order) for i in range(order))
