# flake8: noqa

from .field import Fr
from .polynomial import Polynomial, EvaluationDomain
from .commitment import commit, SRS
from .constraint import ProverInput

from .helpers import (
    custom_hash,
    compute_permutation_challenges,
    vanishing_polynomial,
    get_permutation_part,
    compute_satisfiability_polynomial,
    compute_t2_evalutaion,
    compute_t3_evaluation,
)


def get_public_input(witnesses):
    return witnesses


def prove(prover_input: ProverInput, srs: SRS):
    n = prover_input.number_of_gates()
    witnesses = prover_input.witnesses
    domain_n = EvaluationDomain.from_roots_of_unity(n)
    vanishing = vanishing_polynomial(n)

    # TODO: make it random
    b1, b2, b3, b4, b5, b6, b7, b8, b9 = [Fr(i) for i in range(9)]

    a = Polynomial(b2, b1) * vanishing + domain_4n.inverse_fft(witnesses.a)
    b = Polynomial(b4, b3) * vanishing + domain_4n.inverse_fft(witnesses.b)
    c = Polynomial(b6, b5) * vanishing + domain_4n.inverse_fft(witnesses.c)

    commit_a = commit(a, srs)
    commit_b = commit(b, srs)
    commit_c = commit(c, srs)

    # First output
    yield prover_input.public_inputs, commit_a, commit_b, commit_c

    beta, gamma = compute_permutation_challenges(
        commit_a, commit_b, commit_c, prover_input.public_inputs
    )

    # compute permutation polynomial
    evalutations = get_permutation_part(prover_input, beta, gamma, domain_4n)
    z = domain_4n.inverse_fft(evalutations)  # + noise
    commit_z = commit(z, srs)

    # Second output
    yield commit_z

    # Compute quotient challenge
    alpha = custom_hash(commit_a, commit_b, commit_c, commit_z)

    a_evals = a.fft(domain_4n)
    b_evals = b.fft(domain_4n)
    c_evals = c.fft(domain_4n)

    l1 = vanishing / (Polynomial(-Fr(1), Fr(1)) * Fr(n))  # (x^n - 1)/ ((x - 1) * n)
    satisfiability_evals = compute_satisfiability_polynomial(
        a_evals, b_evals, c_evals, prover_input
    )
    t1 = domain_4n.inverse_fft(satisfiability_evals) * alpha / vanishing

    z_evals = z.fft(domain_4n)

    t2_evals = compute_t2_evalutaion(
        a_evals, b_evals, c_evals, z_evals, alpha, beta, gamma, domain_4n
    )
    t2 = domain_4n.inverse_fft(t2_evals)

    sigma1, sigma2, sigma3 = prover_input.split_permutations()

    z_coset_evals = z.coset_fft(domain_4n)

    t3_evals = compute_t3_evaluation(
        a_evals,
        b_evals,
        c_evals,
        z_coset_evals,
        alpha,
        beta,
        gamma,
        n,
        sigma1,
        sigma2,
        sigma3,
    )

    t3 = domain_4n.inverse_fft(t3_evals)
    t_23 = (t2 - t3) / vanishing

    t4 = (z - Fr(1)) * l1 * (alpha ** 3) / vanishing

    # Compute quotient polynomial
    t = t1 + t_23 + t4
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
