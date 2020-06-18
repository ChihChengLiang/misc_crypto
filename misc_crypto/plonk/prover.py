from .field import Fr, FieldElement, roots_of_unity
from typing import Sequence
from .polynomial import Polynomial, lagrange, EvaluationDomain
from .commitment import commit, SRS
from .constraint import ProverInput

from .helpers import (
    custom_hash,
    compute_permutation_challenges,
    vanishing_polynomial,
    get_permutation_part,
    compute_satisfication_polynomial,
)


def get_public_input(witnesses):
    return witnesses


def prove(prover_input: ProverInput, srs: SRS):
    n = prover_input.number_of_gates()
    witnesses = prover_input.witnesses
    eval_domain = EvaluationDomain.from_roots_of_unity(n)
    vanishing = vanishing_polynomial(n)

    # TODO: make it random
    b1, b2, b3, b4, b5, b6, b7, b8, b9 = [Fr(i) for i in range(9)]

    a = Polynomial(b2, b1) * vanishing + eval_domain.inverse_fft(witnesses.a)
    b = Polynomial(b4, b3) * vanishing + eval_domain.inverse_fft(witnesses.b)
    c = Polynomial(b6, b5) * vanishing + eval_domain.inverse_fft(witnesses.c)

    commit_a = commit(a, srs)
    commit_b = commit(b, srs)
    commit_c = commit(c, srs)

    # First output
    yield prover_input.public_inputs, commit_a, commit_b, commit_c

    beta, gamma = compute_permutation_challenges(
        commit_a, commit_b, commit_c, prover_input.public_inputs
    )

    # compute permutation polynomial
    evalutations = get_permutation_part(prover_input, beta, gamma, eval_domain)
    z = Polynomial(b9, b8, b7) * vanishing + eval_domain.inverse_fft(evalutations)

    commit_z = commit(z, srs)

    # Second output
    yield commit_z

    # Compute quotient challenge
    alpha = custom_hash(commit_a, commit_b, commit_c, commit_z)

    l1 = vanishing / Polynomial(-1, 1) * (1 / Fr(n))  # (x^n - 1)/ (n * (x - 1))
    satisfication = compute_satisfication_polynomial(a, b, c, prover_input, eval_domain)
    # Compute quotient polynomial
    t = (
        satisfication * alpha / vanishing
        + (a + Polynomial(gamma, beta))
        * (b + Polynomial(gamma, beta * k1))
        * (c + Polynomial(gamma, beta * k2) * z)
        * alpha ** 2
        / vanishing
        - (a + beta * sigma1 + gamma)
        * (b + beta * sigma2 + gamma)
        * (c + beta * sigma3 + gamma)
        * z.shift(1)
        * alpha ** 2
        / vanishing
        + (z - 1) * l1 * alpha ** 3 / vanishing
    )
    coeff = t.coefficients
    t_lo = Polynomial(*coeff[:n])
    t_mid = Polynomial(*coeff[n : 2 * n])
    t_hi = Polynomial(*coeff[2 * n :])
    commit_t_lo = commit(t_lo, srs)
    commit_t_mid = commit(t_mid, srs)
    commit_t_hi = commit(t_hi, srs)

    # Third output
    yield commit_t_lo, commit_t_mid, commit_t_hi

    # Compute evaluation challenge
    zz = custom_hash(
        commit_a, commit_b, commit_c, commit_z, commit_t_lo, commit_t_mid, commit_t_hi
    )

    a_eval = a.evaluate(zz)
    b_eval = b.evaluate(zz)
    c_eval = c.evaluate(zz)
    sigma1_eval = sigma1.evaluate(zz)
    sigma2_eval = sigma2.evaluate(zz)
    t_eval = t.evaluate(zz)
    z_eval = z.shift(1).evaluate(zz)

    # Compute linearisation polynomial

    r = (
        (a_eval * b_eval * qm + a_eval * ql + b_eval * qr + c_eval * qo + qc) * alpha
        + (a_eval + beta * zz + gamma)
        * (b_eval + beta * k1 * zz + gamma)
        * (c_eval + beta * k2 * zz + gamma)
        * z
        * alpha ** 2
        - (a_eval + beta * sigma1_eval + gamma)
        * (b_eval + beta * sigma2_eval + gamma)
        * beta
        * z_eval
        * sigma3
        * alpha ** 2
        + z * l1.evaluate(zz) * alpha ** 3
    )
    # Compute linearisation evaluation
    r_eval = r.evaluate(zz)

    # Forth output
    yield a_eval, b_eval, c_eval, sigma1_eval, sigma2_eval, z_eval, t_eval, r_eval

    # Compute opening challenge
    v = custom_hash(
        commit_a,
        commit_b,
        commit_c,
        commit_z,
        commit(t, srs),
        a_eval,
        b_eval,
        c_eval,
        sigma1_eval,
        sigma2_eval,
        z_eval,
        t_eval,
        r_eval,
    )

    # Compute opening polynomial
    wz = (
        (t_lo + (zz ** n) * t_mid + z ** (2 * n) * t_hi - t_eval)
        + v * (r - r_eval)
        + v ** 2 * (a - a_eval)
        + v ** 3 * (b - b_eval)
        + v ** 4 * (c - c_eval)
        + v ** 5 * (sigma1 - sigma1_eval)
        + v ** 6 * (sigma2 - sigma2_eval)
    ) / Polynomial(-zz)

    # Compute opening polynomial
    wz_omega = v ** 7 * (z - zz) / Polynomial(-z * omega)

    commit_wz = commit(wz, srs)
    commit_wz_omega = commit(wz_omega, srs)
    # Fifth output
    yield commit_wz, commit_wz_omega
