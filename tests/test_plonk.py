from misc_crypto.plonk.polynomial import (
    Polynomial,
    lagrange,
    EvaluationDomain,
    permutation_polynomial_evalutations,
)

from misc_crypto.plonk.field import Fr, FQ, roots_of_unity

from misc_crypto.plonk.commitment import (
    srs_setup,
    commit,
    create_witness_same_z,
    verify_evaluation_same_z,
)
from misc_crypto.plonk.constraint import circuit

from misc_crypto.plonk.prover import prove
from misc_crypto.plonk.helpers import pre_proving_check
import pytest


class F13(FQ):
    field_modulus = 13


class F337(FQ):
    field_modulus = 337


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


def test_polynomial_works_on_fields():
    p = Polynomial(Fr(1), Fr(2), Fr(100))
    repr(p)
    p.evaluate(Fr(0))
    p.evaluate(Fr(5))


def test_division():
    a = Polynomial(-288, 0, 2, 1)
    b = Polynomial(-6, 1)
    assert a / b == Polynomial(48, 8, 1)

    a = Polynomial(1, 3, 3, 1)
    b = Polynomial(1, 2, 1)
    assert a / b == Polynomial(1, 1)

    # (x^n -1) / (n*(x-1)) == (1/n)(x^(n-1) +... + 1)
    assert Polynomial(F13(-1), F13(0), F13(0), F13(0), F13(1)) / (
        Polynomial(F13(-1), F13(1)) * 4
    ) == Polynomial(10, 10, 10, 10)


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
    c.calculate_witness(input_mapping)

    gate_vector = c.get_gate_vector()

    assert len(c.wires) == 10
    assert c.num_non_trivial_gates() == 6
    assert len(c.gates) == 8

    # MUL MUL ADD INP ADD INP DUM DUM
    assert gate_vector.a == [3, 9, 3, 5, 30, 35, 0, 0]
    assert gate_vector.b == [3, 3, 27, 0, 5, 0, 0, 0]
    assert gate_vector.c == [9, 27, 30, 5, 35, 35, 0, 0]

    gate_wire_vector = c.get_gate_wire_vector()
    assert gate_wire_vector.a == [0, 1, 0, 4, 3, 7, -1, -1]
    assert gate_wire_vector.b == [0, 0, 2, -1, 5, -1, -1, -1]
    assert gate_wire_vector.c == [1, 2, 3, 5, 6, 8, -1, -1]

    assert c.get_permutation() == (
        [9, 16, 0, 3, 18, 5, 23, 6,]
        + [2, 8, 17, 7, 19, 11, 13, 14,]
        + [1, 10, 4, 12, 20, 21, 15, 22,]
    )
    prover_input = c.get_prover_input()

    assert prover_input.get_public_input_evaluations() == [0, 0, 0, -5, 0, -35, 0, 0]


def test_roots_of_unity():
    roots = roots_of_unity(8)
    assert roots[1] * roots[-1] == 1


def test_fft():

    p = Polynomial(3, 1, 4, 1, 5, 9, 2, 6)
    domain = EvaluationDomain(domain=[F337(85) ** i for i in range(8)])
    assert domain.domain == [1, 85, 148, 111, 336, 252, 189, 226]
    evaluations = p.fft(domain)
    assert evaluations == [31, 70, 109, 74, 334, 181, 232, 4]
    p2 = domain.inverse_fft(evaluations)
    assert p2.coefficients == (3, 1, 4, 1, 5, 9, 2, 6)


def test_fft_2():
    ed = EvaluationDomain.from_roots_of_unity(8)
    evaluations = [3, 9, 3, 5, 30, 35, 0, 0]
    assert ed.inverse_fft(evaluations).fft(ed) == evaluations


def test_coset_fft():
    ed = EvaluationDomain(domain=[F337(85) ** i for i in range(8)])
    p = Polynomial(3, 1, 4, 1, 5, 9, 2)
    assert p.fft(ed) == [25, 62, 323, 247, 3, 189, 18, 168]
    assert p.coset_fft(ed) == [62, 323, 247, 3, 189, 18, 168, 25]


def test_permutation_polynomial_evalutations():
    beta = F13(3)
    gamma = F13(5)
    f_evaluations = [F13(7), F13(8), F13(7)]
    evalutation_domain = [F13(1), F13(2), F13(4)]
    k1 = 2
    s_id_evals = [k1 * d for d in evalutation_domain]
    s_sigma_evals = [2, 1, 0]
    evals = permutation_polynomial_evalutations(
        beta, gamma, f_evaluations, s_id_evals, s_sigma_evals
    )
    assert evals == [1, 1, 4]


@pytest.mark.xfail(reason="Work in progress")
def test_prover():

    srs = srs_setup(64, 5)

    c = circuit()
    input_mapping = {"x": 3, "const": 5, "y": 35}
    c.calculate_witness(input_mapping)
    prover_input = c.get_prover_input()
    assert pre_proving_check(prover_input) is None

    proof = tuple(prove(prover_input, srs))
    print(proof)
