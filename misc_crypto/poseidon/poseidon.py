from eth_utils import to_tuple
from typing import Tuple, Iterator, Sequence
from .constants import DEFAULT_SEED
from .fields import Fr
from .utils import get_constants, get_matrix, recommend_parameter


def ark(state: Sequence[Fr], c: Fr) -> Tuple[Fr, ...]:
    return tuple(s + c for s in state)


def sigma(a: Fr) -> Fr:
    """
    Raise a to a**5
    """
    a_2 = a * a
    a_4 = a_2 * a_2
    return a * a_4


@to_tuple
def mix(state: Tuple[Fr], M: Tuple[Tuple[Fr], ...]) -> Iterator[Fr]:
    """
    Perform inner product: state' = M * state
    """
    for row in range(len(state)):
        accumulation = Fr(0)
        for col, s in enumerate(state):
            accumulation += M[row][col] * s
        yield accumulation


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


# This is the circomlib default Poseidon hash function
poseidon_t6 = Poseidon(6, 8, 57).hash
