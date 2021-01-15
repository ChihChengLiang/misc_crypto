from misc_crypto.ecc import F337
from misc_crypto.polynomial.fft import fft, inverse_fft


def test_fft():

    coefficients = [F337(c) for c in (3, 1, 4, 1, 5, 9, 2, 6)]
    domain = [F337(85) ** i for i in range(8)]
    assert domain == [1, 85, 148, 111, 336, 252, 189, 226]
    evaluations = fft(coefficients, domain)
    assert evaluations == [31, 70, 109, 74, 334, 181, 232, 4]
    assert inverse_fft(evaluations, domain) == coefficients


def test_fft_2():
    a = F337(5)
    p_minus_1 = F337.field_modulus - 1
    order = 8
    domain = tuple(a ** ((i * p_minus_1) // order) for i in range(order))

    evaluations = [F337(c) for c in (3, 9, 3, 5, 30, 35, 0, 0)]
    assert fft(inverse_fft(evaluations, domain), domain) == evaluations
