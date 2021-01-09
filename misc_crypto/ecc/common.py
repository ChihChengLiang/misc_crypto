from .protocol import G1, G2, Backend, FieldElement
from typing import Tuple


def pairing_check(
    backend: Backend, G1_left: G1, G2_left: G2, G1_right: G1, G2_right: G2
) -> bool:
    left = backend.pairing(
        G1_left,
        G2_left,
        final_exponentiate=False,
    )
    right = backend.pairing(
        G1_right,
        G2_right,
        final_exponentiate=False,
    )
    final_exponentiation = backend.final_exponentiate(left * right)
    return final_exponentiation == backend.FQ12One()


def roots_of_unity(backend: Backend, order: int) -> Tuple[FieldElement, ...]:
    # TODO: Check the multiplicative subgroup must have size  2^n
    # TODO: Support fields other than Fr
    a = backend.Fr(5)
    p_minus_1 = backend.field_modulus - 1
    return tuple(a ** ((i * p_minus_1) // order) for i in range(order))
