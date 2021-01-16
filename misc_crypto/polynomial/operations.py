"""
Assumning inputs are all valid polynomial coefficients
"""
from typing import Sequence, List
from misc_crypto.ecc import FieldElement


def add_polynomial(
    a: Sequence[FieldElement], b: Sequence[FieldElement]
) -> List[FieldElement]:
    _long, short = (a, b) if len(a) >= len(b) else (b, a)
    return [_l + _s for _l, _s in zip(_long, short)] + _long[len(short) :]


def naive_multiply(
    a: Sequence[FieldElement], b: Sequence[FieldElement]
) -> List[FieldElement]:
    out_len = len(a) + len(b) - 1
    zero = a[0].zero()

    product = []

    for power in range(out_len):
        _sum = zero
        for i in range(len(a)):
            for j in range(len(b)):
                if i + j == power:
                    _sum += a[i] * b[j]
        product.append(_sum)
    return product


def lagrange(
    domain: Sequence[FieldElement], evaluation: Sequence[FieldElement]
) -> List[FieldElement]:

    if len(domain) != len(evaluation):
        raise ValueError("expect same length")

    one = domain[0].one()

    coefficients = []
    for i, (x, y) in enumerate(zip(domain, evaluation)):
        domain_rest = domain[:i] + domain[i + 1 :]
        basis = [one]
        denominator = one
        for xx in domain_rest:
            basis = naive_multiply(basis, [-xx, one])
            denominator *= x - xx
        basis = [y * b / denominator for b in basis]
        coefficients = add_polynomial(coefficients, basis)
    return coefficients
