from py_ecc.bn128 import curve_order
from py_ecc.fields import FQ
from hashlib import blake2b
from eth_utils import to_tuple
from typing import Tuple


# All the algebra of the circuit must be in the Fr Field
class Fr(FQ):
    field_modulus = curve_order


def little_endian_to_int(_input: bytes) -> int:
    result = 0
    for i, byte in enumerate(_input):
        result += byte << (i*8)
    return result


@to_tuple
def get_pseudo_random(seed: bytes, n: int) -> Tuple[Fr]:
    h = seed
    for _ in range(n):
        h = blake2b(h, digest_size=32).digest()
        yield Fr(little_endian_to_int(h))


def all_different(_tuple: Tuple[Fr]) -> bool:
    _list = list(_tuple)
    for _ in range(len(_tuple)):
        a = _list.pop()
        if a == Fr(0):
            return False
        for b in _list:
            if a == b:
                return False
    return True


@to_tuple
def get_matrix(t: int, seed: bytes) -> Tuple[Tuple[Fr], ...]:
    nonce = 0
    _seed = b''.join([seed,  b'_matrix_', f"{nonce:04d}".encode()])
    cmatrix = get_pseudo_random(_seed, t*t)
    while not all_different(cmatrix):
        nonce += 1
        nonceStr = f"{nonce:04d}" if nonce < 10000 else str(nonce)
        _seed = b''.join([seed,  b'_matrix_', nonceStr])
        cmatrix = get_pseudo_random(_seed, t*t)
    for i in range(t):
        yield tuple(
            Fr(1)/(cmatrix[i]-cmatrix[t+j]) for j in range(t)
        )


class Poseidon:
    seed = "poseidon"
    roundsF = 8
    roundsP = 57
    width = 3

    def __init__(self):
        pass