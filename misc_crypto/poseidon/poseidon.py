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
        result += byte << (i * 8)
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
    _seed = b"".join([seed, b"_matrix_", f"{nonce:04d}".encode()])
    cmatrix = get_pseudo_random(_seed, t * t)
    while not all_different(cmatrix):
        nonce += 1
        nonceStr = f"{nonce:04d}" if nonce < 10000 else str(nonce)
        _seed = b"".join([seed, b"_matrix_", nonceStr])
        cmatrix = get_pseudo_random(_seed, t * t)
    for i in range(t):
        yield tuple(Fr(1) / (cmatrix[i] - cmatrix[t + j]) for j in range(t))


def get_constants(t: int, seed: bytes, rounds: int):
    return get_pseudo_random(seed + b"_constants", rounds)


@to_tuple
def ark(state: Tuple[Fr], c: Fr) -> Tuple[Fr]:
    for s in state:
        yield s + c


def sigma(a: Fr) -> Fr:
    """
    Raise a to a**5
    """
    a_2 = a * a
    a_4 = a_2 * a_2
    return a * a_4


@to_tuple
def mix(state: Tuple[Fr], M: Tuple[Tuple[Fr], ...]) -> Tuple[Fr]:
    """
    Perform inner product: state' = M * state
    """
    for row in range(len(state)):
        result = Fr(0)
        for col, s in enumerate(state):
            result = result + M[row][col] * s
        yield result


class Poseidon:
    seed: bytes
    roundsF: int
    roundsP: int
    t: int
    matrix: Tuple[Tuple[Fr], ...]
    constants: Tuple[Fr]

    def __init__(self, t: int, roundsF: int, roundsP: int, seed=b"poseidon") -> None:
        self.t = t
        self.roundsF = roundsF
        self.roundsP = roundsP
        self.seed = seed
        self.matrix = get_matrix(t, seed)
        self.constants = get_constants(t, seed, roundsF + roundsP)

    def hash(self, inputs: Tuple[Fr]):
        len_inputs = len(inputs)
        if len_inputs > self.t:
            raise ValueError(
                (
                    "Length of inputs should be less than t."
                    f"Got len(inputs): {len_inputs} "
                    f"t: {self.t}"
                )
            )
        if len_inputs == 0:
            raise ValueError("Input shouldn't be empty")

        # Initial state is inputs padded with zeros to length t
        state = tuple(inputs) + (Fr(0),) * (self.t - len_inputs)

        halfF = self.roundsF / 2
        for i in range(self.roundsF + self.roundsP):
            state = ark(state, self.constants[i])
            if i < halfF or i >= halfF + self.roundsP:
                # Full S-Box layer round
                state = tuple(sigma(s) for s in state)
            else:
                # Partial S-Box layer round
                state = (sigma(state[0]),) + state[1:]
            state = mix(state, self.matrix)
        return state[0]


poseidon_t6 = Poseidon(6, 8, 57).hash