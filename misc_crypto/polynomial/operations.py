"""
Assumning inputs are all valid polynomial coefficients
"""
from typing import Sequence, List, Tuple
from misc_crypto.ecc import FieldElement
from misc_crypto.polynomial.helpers import next_power_of_2
from misc_crypto.ecc import roots_of_unity, Backend
from misc_crypto.polynomial.fft import fft, inverse_fft


def remove_leading_zeros(a: Sequence[FieldElement]) -> List[FieldElement]:
    result = a.copy()
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return result


def is_zero(a: Sequence[FieldElement]) -> bool:
    return len(a) == 1 and a[0] == 0


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


def fft_multiply(
    backend: Backend, a: Sequence[FieldElement], b: Sequence[FieldElement]
) -> List[FieldElement]:
    domain_size = next_power_of_2(len(a) + len(b) - 1)
    domain = roots_of_unity(backend, domain_size)
    a_evaluations = fft(a, domain)
    b_evaluations = fft(b, domain)

    product_evaluations = [_a * _b for _a, _b in zip(a_evaluations, b_evaluations)]
    product_coefficients = inverse_fft(product_evaluations, domain)

    return remove_leading_zeros(product_coefficients)


def fft_multiply_many(
    backend: Backend, ps: Sequence[Sequence[FieldElement]]
) -> List[FieldElement]:
    output_degree = sum([len(p) - 1 for p in ps])
    domain_size = next_power_of_2(output_degree + 1)
    domain = roots_of_unity(backend, domain_size)
    evaluations = [fft(p, domain) for p in ps]
    one = ps[0][0].one()
    product_evaluations = []
    for i in range(len(domain)):
        product = one
        for evaluation in evaluations:
            product *= evaluation[i]
        product_evaluations.append(product)
    product_coefficients = inverse_fft(product_evaluations, domain)

    return remove_leading_zeros(product_coefficients)


def euclidean_division(
    dividend: Sequence[FieldElement], divisor: Sequence[FieldElement]
) -> Tuple[List[FieldElement], List[FieldElement]]:

    if is_zero(divisor):
        raise ZeroDivisionError

    len_divisor = len(divisor)
    remainder_degree = len(dividend) - len_divisor

    if remainder_degree < 0:
        raise ValueError("divisor has higher degree:", dividend, divisor)

    # Work with reverse order
    quotient = []
    remainder = list(reversed(dividend))
    _divisor = list(reversed(divisor))

    for _ in range(remainder_degree + 1):
        m = remainder[0] / _divisor[0]
        affected = [r - m * d for r, d in zip(remainder[1:], _divisor[1:])]
        remainder = affected + remainder[len_divisor:]
        quotient.append(m)

    return (
        remove_leading_zeros(list(reversed(quotient))),
        remove_leading_zeros(list(reversed(remainder))),
    )


def true_division(
    dividend: Sequence[FieldElement], divisor: Sequence[FieldElement]
) -> List[FieldElement]:
    quotient, remainder = euclidean_division(dividend, divisor)
    if not is_zero(remainder):
        raise ValueError("Not divisible  remainder", remainder)
    return quotient


def evaluate(p: Sequence[FieldElement], x: FieldElement) -> FieldElement:
    power = x
    result = p[0]
    for coefficient in p[1:]:
        result += coefficient * power
        power *= x
    return result


def compute_zero_polynomial(zs: Sequence[FieldElement]) -> List[FieldElement]:
    z0, z_rest = zs[0], zs[1:]
    one = z0.one()
    zero_polynomial = [-z0, one]
    for z in z_rest:
        zero_polynomial = naive_multiply(zero_polynomial, [-z, one])
    return zero_polynomial


def negate(p: Sequence[FieldElement]) -> List[FieldElement]:
    return [-p_i for p_i in p]
