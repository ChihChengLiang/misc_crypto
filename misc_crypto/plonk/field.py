from typing import Tuple
from misc_crypto.ecc import FieldElement  # noqa: F401
from py_ecc.optimized_bn128 import (  # noqa: F401
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


def roots_of_unity(order: int) -> Tuple[Fr, ...]:
    # TODO: Check the multiplicative subgroup must have size  2^n
    # TODO: Support fields other than Fr
    a = Fr(5)
    p = Fr.field_modulus - 1
    return tuple(a ** ((i * p) // order) for i in range(order))
