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
    a_evals, b_evals, c_evals, prover_input: ProverInput
) -> Polynomial:
    qm, ql, qr, qo, qc = prover_input.flatten_selectors()
    public_inputs_evaluations = prover_input.get_public_input_evaluations()
    results = []
    for aev, bev, cev, m, l, r, o, c, pi in zip(
        a_evals, b_evals, c_evals, qm, ql, qr, qo, qc, public_inputs_evaluations
    ):
        result = aev * bev * m + aev * l + bev * r + cev * o + pi + c
        results.append(result)
    return results


def compute_t2_evalutaion(
    a_evals,
    b_evals,
    c_evals,
    z_evals,
    alpha,
    beta,
    gamma,
    evalutaion_domain: EvaluationDomain,
):
    results = []
    alpha_square = alpha * alpha

    for a, b, c, z, d in zip(
        a_evals, b_evals, c_evals, z_evals, evalutaion_domain.domain
    ):
        aa = a + d * beta + gamma
        bb = b + d * beta * K1 + gamma
        cc = c + d * beta * K2 + gamma

        results.append(aa * bb * cc * z * alpha_square)
    return results


def compute_t3_evaluation(
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
):
    results = []
    alpha_square = alpha * alpha

    for i in range(4 * n):
        if i < n:
            aa = a_evals[i] + sigma1[i] * beta + gamma
            bb = b_evals[i] + sigma2[i] * beta + gamma
            cc = c_evals[i] + sigma3[i] * beta + gamma
        else:
            aa = a_evals[i] + gamma
            bb = b_evals[i] + gamma
            cc = c_evals[i] + gamma
        results.append(aa * bb * cc * z_coset_evals[i] * alpha_square)
    return results


def pre_proving_check(prover_input: ProverInput):
    n = prover_input.number_of_gates()
    wa, wb, wc = prover_input.split_witnesses()
    permutation = prover_input.permutation
    qm, ql, qr, qo, qc = prover_input.flatten_selectors()
    public_inputs = prover_input.get_public_input_evaluations()
    for i in range(n):
        satisfiability = (
            wa[i] * wb[i] * qm[i]
            + wa[i] * ql[i]
            + wb[i] * qr[i]
            + wc[i] * qo[i]
            + public_inputs[i]  # Really?
            + qc[i]
        )
        if satisfiability != 0:
            raise ValueError(
                (
                    f"Satisfiability doesn't meet at gate {i}.\n"
                    f"Expect: a * b * qm + a * ql + b * qr + c * qo + pi + qc == 0\n"
                    f"Got:    {wa[i]} * {wb[i]} * {qm[i]} + {wa[i]} * {ql[i]} + {wb[i]} * {qr[i]} + {wc[i]} * {qo[i]} + {public_inputs[i]} + {qc[i]} != 0"
                )
            )
    witnesses = wa + wb + wc
    for i, p in enumerate(permutation):
        wi, wp = witnesses[i], witnesses[p]
        if wi != wp:
            raise ValueError(
                f"Bad permutation {i} -> {p}, where witnesses are {wi} and {wp}"
            )
