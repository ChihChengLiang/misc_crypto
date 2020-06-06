from misc_crypto.plonk.polynomial import Polynomial, lagrange


def test_polynomial():

    ps = [Polynomial(), Polynomial(-1), Polynomial(1, 1), Polynomial(1, -11, 1, -1, 1)]
    for p in ps:
        repr(p)


def test_polynomial_evaluation():
    assert Polynomial(1, 1, 1).evaluate(2) == 7
    assert Polynomial(-2, 7, -5, 1).evaluate(0) == -2
    assert Polynomial(-2, 7, -5, 1).evaluate(1) == 1
    assert Polynomial(-2, 7, -5, 1).evaluate(2) == 0
    assert Polynomial(-2, 7, -5, 1).evaluate(3) == 1


def test_polynomial_addition():
    assert Polynomial(1, 1, 1).add(Polynomial(1, 1, 1)) == Polynomial(2, 2, 2)


def test_polynomial_multiplication():
    assert Polynomial(1, 1) * Polynomial(1, 1) == Polynomial(1, 2, 1)

def test_lagrange():
    assert lagrange([0, 1, 2], [0, 1, 8]) == Polynomial(0, -2, 3)