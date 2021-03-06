"""
Fast Fourier Transform:
See https://vitalik.ca/general/2019/05/12/fft.html for motivation
"""
from typing import Sequence
from .field import FieldElement, Fr
from .utils import is_power_of_2


def fft(
    coefficients: Sequence[FieldElement], domain: Sequence[FieldElement]
) -> Sequence[FieldElement]:
    len_coeff, len_domain = len(coefficients), len(domain)

    if not is_power_of_2(len_domain):
        raise ValueError("length of domain should be a power of 2, got", len_domain)

    if len_coeff > len_domain:
        raise ValueError(
            (
                f"The number of coefficients ({len_coeff}) should not be larger than "
                f"the length of domain ({len_domain})"
            )
        )
    padded_coefficients = tuple(coefficients) + (Fr(0),) * (len_domain - len_coeff)

    return _fft(padded_coefficients, domain)


def _fft(
    coefficients: Sequence[FieldElement], domain: Sequence[FieldElement]
) -> Sequence[FieldElement]:
    if len(coefficients) == 1:
        return coefficients
    evens = fft(coefficients[::2], domain[::2])
    odds = fft(coefficients[1::2], domain[::2])
    left_output = []
    right_output = []
    for even, odd, x in zip(evens, odds, domain):
        x_odd = x * odd
        left_output.append(even + x_odd)
        right_output.append(even - x_odd)
    return left_output + right_output


def inverse_fft(
    evaluations: Sequence[FieldElement], domain: Sequence[FieldElement]
) -> Sequence[FieldElement]:
    values = fft(evaluations, domain)
    len_values = len(values)
    return [v / len_values for v in [values[0]] + values[1:][::-1]]
