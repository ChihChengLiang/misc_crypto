from .polynomial import Polynomial
import hashlib
from py_ecc.bls.point_compression import compress_G1
from .field import FQ

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
    return m.digest()


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
