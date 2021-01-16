from typing import Sequence, Tuple, List
from misc_crypto.ecc import Backend, G1, G2, FieldElement, pairing_check
import secrets
from dataclasses import dataclass
from .operations import (
    evaluate,
    add_polynomial,
    true_division,
    lagrange,
    negate,
    compute_zero_polynomial,
)


@dataclass
class SRS:
    toxic: FieldElement  # useful for debugging
    G1: G1
    G2: G2
    G1s: Sequence[G1]
    G2s: Sequence[G2]


def untrusted_setup(backend: Backend, length: int):
    _s = secrets.randbelow(backend.field_modulus)
    s = backend.Fr(_s)
    G1 = backend.get_G1()
    G2 = backend.get_G2()
    G1s = []
    G2s = []
    for i in range(1, length):
        s_i = s ** i
        G1s.append(G1.multiply(s_i))
        G2s.append(G2.multiply(s_i))
    srs = SRS(toxic=s, G1=G1, G2=G2, G1s=G1s, G2s=G2s)
    return srs


def evaluate_on_G1(srs: SRS, p: Sequence[FieldElement]) -> "G1":
    p0, p_rest = p[0], p[1:]
    _sum = srs.G1.multiply(p0)
    for G1s_i, p_i in zip(srs.G1s, p_rest):
        _sum = _sum.add(G1s_i.multiply(p_i))
    return _sum


def evaluate_on_G2(srs: SRS, p: Sequence[FieldElement]) -> "G1":
    p0, p_rest = p[0], p[1:]
    _sum = srs.G2.multiply(p0)
    for G1s_i, p_i in zip(srs.G2s, p_rest):
        _sum = _sum.add(G1s_i.multiply(p_i))
    return _sum


def commit(srs: SRS, p: Sequence[FieldElement]) -> "G1":
    return evaluate_on_G1(srs, p)


def prove_single(
    srs: SRS, p: Sequence[FieldElement], z: FieldElement
) -> Tuple[FieldElement, G1]:
    one = z.one()
    y = evaluate(p, z)
    numerator = add_polynomial(p, [-y])
    q = true_division(numerator, [-z, one])
    return y, evaluate_on_G1(srs, q)


def verify_single(
    backend: Backend,
    srs: SRS,
    commitment: G1,
    z: FieldElement,
    y: FieldElement,
    proof: G1,
) -> bool:
    """
    e(proof, [s - z]_2) ==  e(C - [y]_1, G2)
    """
    neg_z_on_G2 = srs.G2.multiply(-z)
    s_minus_z = srs.G2s[0].add(neg_z_on_G2)
    neg_y_on_G1 = srs.G1.multiply(-y)
    commitment_minus_y = commitment.add(neg_y_on_G1)
    return pairing_check(backend, proof, s_minus_z, commitment_minus_y, srs.G2.neg())


def prove_multiple(
    srs: SRS, p: Sequence[FieldElement], zs: Sequence[FieldElement]
) -> Tuple[FieldElement, G1]:
    ys = [evaluate(p, z) for z in zs]
    interpolation = lagrange(zs, ys)
    zero_polynomial = compute_zero_polynomial(zs)
    numerator = add_polynomial(p, negate(interpolation))
    q = true_division(numerator, zero_polynomial)
    return ys, evaluate_on_G1(srs, q)


def verify_multiple(
    backend: Backend,
    srs: SRS,
    commitment: G1,
    zs: Sequence[FieldElement],
    ys: Sequence[FieldElement],
    proof: G1,
) -> bool:
    """
    e(proof, [Z(s)]_2) ==  e(C - [I(s)]_1, G2)
    """
    zero_polynomial = compute_zero_polynomial(zs)
    zs_on_G2 = evaluate_on_G2(srs, zero_polynomial)
    interpolation = lagrange(zs, ys)
    interpolation_on_G1 = evaluate_on_G1(srs, interpolation)
    c_minus_i = commitment.add(interpolation_on_G1.neg())
    return pairing_check(backend, proof, zs_on_G2, c_minus_i, srs.G2.neg())


def build_polynomial_from_vector(
    backend: Backend, vector: Sequence[FieldElement]
) -> List[FieldElement]:
    domain = [backend.Fr(i) for i in range(len(vector))]
    polynomial = lagrange(domain, vector)
    return polynomial
