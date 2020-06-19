from .polynomial import (
    Polynomial,
    permutation_polynomial_evalutations,
    EvaluationDomain,
)
import hashlib
from py_ecc.bls.point_compression import compress_G1
from .field import FQ, FieldElement, Fr
from .constraint import ProverInput
from .constants import K1, K2
from typing import Sequence


def custom_hash(*args) -> bytes:
    m = hashlib.sha256()
    for arg in args:
        if isinstance(arg, tuple) and len(arg) == 3:
            m.update(compress_G1(arg).to_bytes(48, "big", signed=False))
        elif isinstance(arg, int):
            m.update(arg.to_bytes(8, "big", signed=False))
        elif isinstance(arg, FQ):
            m.update(arg.n.to_bytes(32, "big", signed=False))
        else:
            m.update(arg)
    hash_in_bytes = m.digest()
    hash_in_Fr = Fr(int.from_bytes(hash_in_bytes, "big"))
    return hash_in_Fr


def compute_permutation_challenges(commit_a, commit_b, commit_c, public_inputs):
    beta = custom_hash(commit_a, commit_b, commit_c, *public_inputs)
    gamma = custom_hash(commit_a, commit_b, commit_c, *public_inputs, beta)
    return beta, gamma


def vanishing_polynomial(n: int):
    """
    Z_H(X) := X^n - 1
    """
    return Polynomial(*([-1] + [0] * (n - 1) + [1]))


def get_permutation_part(
    prover_input: ProverInput,
    beta: FieldElement,
    gamma: FieldElement,
    eval_domain: EvaluationDomain,
) -> Sequence[FieldElement]:
    a, b, c = prover_input.split_witnesses()
    sigma_1, sigma_2, sigma_3 = prover_input.split_permutations()
    s_id_1 = [d for d in eval_domain.domain]
    s_id_2 = [K1 * d for d in eval_domain.domain]
    s_id_3 = [K2 * d for d in eval_domain.domain]

    evaluations_1 = permutation_polynomial_evalutations(beta, gamma, a, s_id_1, sigma_1)
    evaluations_2 = permutation_polynomial_evalutations(beta, gamma, b, s_id_2, sigma_2)
    evaluations_3 = permutation_polynomial_evalutations(beta, gamma, c, s_id_3, sigma_3)

    products = [
        ev_1 * ev_2 * ev_3
        for ev_1, ev_2, ev_3 in zip(evaluations_1, evaluations_2, evaluations_3)
    ]
    return products


def compute_satisfiability_polynomial(
    a, b, c, prover_input: ProverInput, eval_domain: EvaluationDomain
) -> Polynomial:
    qm, ql, qr, qo, qc = prover_input.flatten_selectors()
    public_inputs_evaluations = prover_input.get_public_input_evaluations()
    a_evals = a.fft(eval_domain)
    b_evals = b.fft(eval_domain)
    c_evals = c.fft(eval_domain)
    results = []
    for aev, bev, cev, m, l, r, o, c, pi in zip(
        a_evals, b_evals, c_evals, qm, ql, qr, qo, qc, public_inputs_evaluations
    ):
        result = aev * bev * m + aev * l + bev * r + cev * o + pi + c
        results.append(result)
    return eval_domain.inverse_fft(results)
