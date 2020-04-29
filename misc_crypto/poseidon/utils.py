from itertools import count
from eth_utils import to_tuple
from typing import Tuple, Iterator, Sequence
from hashlib import blake2b
from .fields import Fr


@to_tuple
def get_pseudo_random(seed: bytes, n: int) -> Iterator[Fr]:
    h = seed
    for _ in range(n):
        h = blake2b(h, digest_size=32).digest()
        yield Fr(int.from_bytes(h, "little"))


def all_different(_tuple: Sequence[Fr]) -> bool:
    _list = list(_tuple)
    for _ in range(len(_tuple)):
        a = _list.pop()
        if a == Fr(0):
            return False
        for b in _list:
            if a == b:
                return False
    return True


def _get_new_seed(seed: bytes, nonce: int):
    nonce_bytes = f"{nonce:04d}".encode() if nonce < 10000 else bytes(nonce)
    return seed + b"_matrix_" + nonce_bytes


@to_tuple
def get_matrix(t: int, seed: bytes) -> Iterator[Tuple[Fr, ...]]:
    # iterate to get a cmatrix whose elements are all different
    for nonce in count(0):
        _seed = _get_new_seed(seed, nonce)
        cmatrix = get_pseudo_random(_seed, t * t)
        if all_different(cmatrix):
            break

    for i in range(t):
        yield tuple(Fr(1) / (cmatrix[i] - cmatrix[t + j]) for j in range(t))


def get_constants(t: int, seed: bytes, rounds: int):
    return get_pseudo_random(seed + b"_constants", rounds)


def recommend_parameter(elements_length: int) -> Tuple[int, int, int]:
    """
    A faster way to get recommended parameters from the result of running parameter_finder.py.
    """
    if elements_length < 2:
        raise ValueError("Number of elements should be at least 2")

    # Poseidon requires 1 width to be reserved for security.
    t = elements_length + 1
    roundsF = 8
    if t == 3:
        roundsP = 49
    elif t <= 7:
        roundsP = 50
    elif t <= 14:
        roundsP = 51
    elif t <= 29:
        roundsP = 52
    else:
        raise ValueError(
            "Unsupported elements_length, please run parameter_finder.py to get the parameter"
        )
    return t, roundsF, roundsP
