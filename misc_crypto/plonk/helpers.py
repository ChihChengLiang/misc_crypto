from .polynomial import Polynomial


def custom_hash(*args):
    return "hash"

def compute_permutation_challenges(commit_a, commit_b, commit_c, public_inputs):
    beta = custom_hash(commit_a, commit_b, commit_c, *public_inputs)
    gamma = custom_hash(commit_a, commit_b, commit_c, *public_inputs, beta)
    return beta, gamma


# Z_H
def vanishing_polynomial(n: int):
    """
    X^n - 1
    """
    return Polynomial(*([-1] + [0] * (n - 1) + [1]))
