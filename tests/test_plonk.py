from misc_crypto.plonk.polynomial import (
    Polynomial,
    lagrange,
    coordinate_pair_accumulator,
)

from misc_crypto.plonk.field import Fr

from misc_crypto.plonk.commitment import (
    srs_setup,
    commit,
    create_witness_same_z,
    verify_evaluation_same_z,
)
from misc_crypto.plonk.constraint import circuit


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
    assert Polynomial(1, 1, 1) + (Polynomial(1, 1, 1)) == Polynomial(2, 2, 2)


def test_polynomial_multiplication():
    assert Polynomial(1, 1) * Polynomial(1, 1) == Polynomial(1, 2, 1)


def test_lagrange():
    assert lagrange([0, 1, 2], [0, 1, 8]) == Polynomial(0, -2, 3)
    assert lagrange([Fr(0), Fr(1), Fr(2)], [Fr(0), Fr(1), Fr(8)]) == Polynomial(
        Fr(0), Fr(-2), Fr(3)
    )


def test_coordinate_pair_accumulator():
    x = Polynomial(0, 1)
    y = Polynomial(-2, 7, -5, 1)

    p = coordinate_pair_accumulator(x, y, 5, 3, 2)
    assert p.evaluate(4) == -240


def test_polynomial_works_on_fields():
    p = Polynomial(Fr(1), Fr(2), Fr(100))
    repr(p)
    p.evaluate(Fr(0))
    p.evaluate(Fr(5))


def test_division():
    a = Polynomial(-288, 0, 2, 1)
    b = Polynomial(-6, 1)
    assert a / b == Polynomial(48, 8, 1)


def test_polynomial_commitment_same_z():
    d = 5
    secret = 5

    ps = [
        Polynomial(Fr(5), Fr(3)),
        Polynomial(Fr(1), Fr(2)),
        Polynomial(Fr(0), Fr(6), Fr(9)),
    ]

    z = Fr(100)
    gamma = Fr(7)

    srs = srs_setup(d, secret)

    commitments = [commit(p, srs) for p in ps]
    evaluations = [p.evaluate(z) for p in ps]

    witness = create_witness_same_z(polynomials=ps, gamma=gamma, z=z, srs=srs)
    assert verify_evaluation_same_z(
        commitments=commitments,
        gamma=gamma,
        evaluations=evaluations,
        z=z,
        witness=witness,
        srs=srs,
    )


def test_circuit():
    c = circuit()
    c.print()

    input_mapping = {"x": 3, "const": 5, "y": 35}
    gate_vector, selectors = c.calculate_witness(input_mapping)

    assert gate_vector.a == [3, 3, 9, 3, 5, 30, 35]
    assert gate_vector.b == [0, 3, 3, 27, 0, 5, 0]
    assert gate_vector.c == [3, 9, 27, 30, 5, 35, 35]

    print(selectors)
