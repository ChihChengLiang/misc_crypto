from typing import Tuple, Iterator, Sequence
from .constants import DEFAULT_SEED
from .fields import Fr
from .utils import get_constants, get_matrix, recommend_parameter
from .hash import poseidon_hash
from .contract import create_code, ABI
from eth_utils import decode_hex


class Poseidon:
    seed: bytes
    roundsF: int
    roundsP: int
    t: int
    matrix: Tuple[Tuple[Fr, ...], ...]
    constants: Tuple[Fr]

    def __init__(self, t: int, roundsF: int, roundsP: int, seed=DEFAULT_SEED) -> None:
        self.t = t
        self.roundsF = roundsF
        self.roundsP = roundsP
        self.seed = seed
        self.matrix = get_matrix(t, seed)
        self.constants = get_constants(t, seed, roundsF + roundsP)

    @classmethod
    def from_elements_length(cls, elements_length: int):
        t, roundsF, roundsP = recommend_parameter(elements_length)
        return cls(t, roundsF, roundsP)

    def __repr__(self):
        return f"Poseidon(t={self.t}, roundsF={self.roundsF}, roundsP={self.roundsP}, seed={self.seed})"

    def hash(self, inputs: Sequence[Fr]) -> Fr:
        return poseidon_hash(
            self.t, self.roundsF, self.roundsP, self.matrix, self.constants, inputs
        )

    def build_contract(self):
        hexcode = create_code(
            self.t, self.roundsF, self.roundsP, self.matrix, self.constants
        )
        bytecode = decode_hex(hexcode)
        return bytecode, ABI


# This is the circomlib default Poseidon hash function
poseidon_t6 = Poseidon(6, 8, 57).hash
