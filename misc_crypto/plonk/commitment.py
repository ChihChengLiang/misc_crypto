from .field import G1, G2, multiply, FieldElement, pairing_check, neg, Fr, add, Z1
from typing import Sequence, Tuple
from .polynomial import Polynomial
from dataclasses import dataclass


class Commitment:
    value: G1


@dataclass
class SRS:
    powers_of_g1: Tuple["G1", ...]
    g2: G2
    g2_to_secret: G2


def srs_setup(d: int, secret: int) -> SRS:
    powers_of_g1 = [G1]
    power_of_x = 1
    for _ in range(d - 1):
        power_of_x *= secret
        powers_of_g1.append(multiply(G1, power_of_x))
    g2_to_secret = multiply(G2, secret)
    return SRS(powers_of_g1=powers_of_g1, g2=G2, g2_to_secret=g2_to_secret)


def commit(f: Polynomial, srs: SRS) -> "G1":
    len_coeff = len(f.coefficients)
    len_powers_of_g1 = len(srs.powers_of_g1)
    if len_coeff > len_powers_of_g1:
        raise ValueError(
            (
                "The order of polynomial is too high,"
                "expect len(f.coefficients)<=len(srs.powers_of_g1)",
                f"got len(f.coefficients)={len_coeff} and len(srs.powers_of_g1)={len_powers_of_g1}",
            )
        )
    result = Z1
    for coeff, g1_to_x in zip(f.coefficients, srs.powers_of_g1):
        result = add(result, multiply(g1_to_x, coeff.n))
    return result


def create_witness_same_z(
    polynomials: Sequence[Polynomial], gamma: FieldElement, z: FieldElement, srs: SRS,
) -> "G1":
    h = Polynomial(Fr.zero())
    power_of_gamma = 1
    for p in polynomials:
        power_of_gamma *= gamma
        h += (p - p.evaluate(z)) * power_of_gamma
    h /= Polynomial(-z, Fr.one())
    return commit(h, srs)


def verify_evaluation_same_z(
    commitments: Sequence["G1"],
    gamma: FieldElement,
    evaluations: Sequence[FieldElement],
    z: FieldElement,
    witness: "G1",
    srs: SRS,
):
    F = Z1
    power_of_gamma = 1
    v_coeff = 0
    for commitment, evaluation in zip(commitments, evaluations):
        power_of_gamma *= gamma
        F = add(F, multiply(commitment, power_of_gamma.n))
        v_coeff += power_of_gamma * evaluation
    v = multiply(G1, v_coeff.n)
    x_sub_z_in_G2 = add(srs.g2_to_secret, multiply(G2, (-z).n))

    return pairing_check(add(F, neg(v)), G2, neg(witness), x_sub_z_in_G2)
