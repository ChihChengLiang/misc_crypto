from misc_crypto.plonk.polynomial import Polynomial


def test_polynomial():

    ps = [Polynomial(), Polynomial(-1), Polynomial(1, 1), Polynomial(1, -11, 1, -1, 1)]
    for p in ps:
        print(p)


def test_polynomial_evaluation():
    assert Polynomial(1, 1, 1).evaluate(2) == 7
    assert Polynomial(-2, 7, -5, 1).evaluate(0) == -2
    assert Polynomial(-2, 7, -5, 1).evaluate(1) == 1
    assert Polynomial(-2, 7, -5, 1).evaluate(2) == 0
    assert Polynomial(-2, 7, -5, 1).evaluate(3) == 1
