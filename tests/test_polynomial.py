import pytest
from misc_crypto.ecc import F337, BLS12381Backend
from misc_crypto.polynomial.fft import fft, inverse_fft
from misc_crypto.polynomial.operations import (
    add_polynomial,
    fft_multiply,
    fft_multiply_many,
    lagrange,
    naive_multiply,
    euclidean_division,
    true_division,
    evaluate,
)
from misc_crypto.polynomial.commitments import (
    commit,
    prove_single,
    untrusted_setup,
    verify_single,
    prove_multiple,
    verify_multiple,
    build_polynomial_from_vector,
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


def test_fft_multiply_many():
    backend = BLS12381Backend
    a = [backend.Fr(x) for x in [1, 1]]
    b = [backend.Fr(x) for x in [2, 1]]
    c = [backend.Fr(x) for x in [3, 1]]
    ab = fft_multiply(backend, a, b)
    abc = fft_multiply(backend, ab, c)
    assert fft_multiply_many(backend, [a, b, c]) == abc


def test_euclidean_division():
    a1 = [F337(c) for c in [1, 3, 3, 1]]
    b1 = [F337(c) for c in [1, 2, 1]]
    quotient = [1, 1]
    assert euclidean_division(a1, b1) == (quotient, [0])

    a2 = [F337(c) for c in [7, 5, 3, 1]]
    assert euclidean_division(a2, b1) == (quotient, [6, 2])

    assert true_division(a1, b1) == quotient
    with pytest.raises(ValueError):
        true_division(a2, b1)


def test_evaluate():
    p = [F337(c) for c in [1, 3, 3, 1]]
    x = F337(2)
    assert evaluate(p, x) == F337(27)


def test_commitments():
    backend = BLS12381Backend
    srs = untrusted_setup(backend, 10)

    p = [backend.Fr(x) for x in [1, 2, 3, 4]]

    commitment = commit(srs, p)

    z = backend.Fr(5)

    y, proof = prove_single(srs, p, z)

    assert verify_single(backend, srs, commitment, z, y, proof)

    zs = [backend.Fr(x) for x in [2, 4, 6]]
    ys, proof = prove_multiple(srs, p, zs)
    assert verify_multiple(backend, srs, commitment, zs, ys, proof)


def test_vector_commitment():
    backend = BLS12381Backend
    srs = untrusted_setup(backend, 20)
    vector = [backend.Fr(v) for v in [55, 66, 55, 100, 21, 1, 2, 3, 4, 5, 891038103]]
    p = build_polynomial_from_vector(backend, vector)

    commitment = commit(srs, p)
    zs = [backend.Fr(i) for i in [0, 2, 3, 5, 7]]

    ys, proof = prove_multiple(srs, p, zs)
    assert ys == [evaluate(p, z) for z in zs]
    assert verify_multiple(backend, srs, commitment, zs, ys, proof)
