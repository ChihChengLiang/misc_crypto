from py_ecc.bn128 import curve_order
from py_ecc.fields import FQ
from hashlib import blake2b
from eth_utils import to_tuple
from typing import Tuple


# All the algebra of the circuit must be in the Fr Field
class Fr(FQ):
    field_modulus = curve_order


def littleEndianToInt(_input: bytes) -> int:
    result = 0
    for i, byte in enumerate(_input):
        result += byte << (i*8)
    return result


@to_tuple
def getPseudoRandom(seed: bytes, n: int) -> Tuple[int]:
    h = seed
    for _ in range(n):
        h = blake2b(h, digest_size=32).digest()
        yield Fr(littleEndianToInt(h))


class Poseidon:
    seed = "poseidon"
    roundsF = 8
    roundsP = 57
    width = 3

    def __init__(self):
        pass

    def getPseudoRandom(self):
        pass

    def getMatrix(self):
        pass

    def getConstants(self):
        pass
