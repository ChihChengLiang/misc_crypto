from misc_crypto.ecc import F337, BLS12381Backend
from misc_crypto.polynomial.fft import fft, inverse_fft
from misc_crypto.polynomial.operations import (
    add_polynomial,
    fft_multiply,
    lagrange,
    naive_multiply,
)


def test_add_polynomial():
    a = [F337(x) for x in [1, 2, 3]]
    b = [F337(x) for x in [1, 2, 3, 4, 5, 6, 7]]
    _sum = [F337(x) for x in [2, 4, 6, 4, 5, 6, 7]]
    assert add_polynomial(a, b) == add_polynomial(b, a) == _sum


def test_naive_multiply():
    a = [F337(x) for x in [1, 2, 3]]
    b = [F337(x) for x in [4, 5, 6]]
    #           3   2   1
    #           6   5   4
    # --------------------
    #           12   8   4
    #       15  10   5
    # 18    12  6
    # --------------------
    # 18    27  28   13  4
    product = [F337(x) for x in [4, 13, 28, 27, 18]]
    assert naive_multiply(a, b) == naive_multiply(b, a) == product


def test_lagrange():
    # 1 + 2x + 3x^2 + x^3
    coefficients = [F337(c) for c in [1, 2, 3, 1]]
    domain = [F337(x) for x in [0, 1, 2, 3]]

    evaluations = [F337(x) for x in [1, 7, 25, 61]]

    assert coefficients == lagrange(domain, evaluations)


def test_fft():

    coefficients = [F337(c) for c in (3, 1, 4, 1, 5, 9, 2, 6)]
    domain = [F337(85) ** i for i in range(8)]
    assert domain == [1, 85, 148, 111, 336, 252, 189, 226]
    evaluations = fft(coefficients, domain)
    assert evaluations == [31, 70, 109, 74, 334, 181, 232, 4]
    assert (
        inverse_fft(evaluations, domain)
        == coefficients
        == lagrange(domain, evaluations)
    )


def test_fft_2():
    a = F337(5)
    p_minus_1 = F337.field_modulus - 1
    order = 8
    domain = tuple(a ** ((i * p_minus_1) // order) for i in range(order))

    evaluations = [F337(c) for c in (3, 9, 3, 5, 30, 35, 0, 0)]
    assert fft(inverse_fft(evaluations, domain), domain) == evaluations


def test_fft_multiply():
    backend = BLS12381Backend
    a = [backend.Fr(c) for c in [1, 2, 3, 4]]
    b = [backend.Fr(c) for c in [5, 6, 7, 8]]
    assert (
        fft_multiply(backend, a, b)
        == fft_multiply(backend, b, a)
        == naive_multiply(a, b)
    )
