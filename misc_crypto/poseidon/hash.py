from eth_utils import to_tuple
from typing import Sequence, Tuple, Iterator
from .fields import Fr


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
def mix(state: Sequence[Fr], matrix: Sequence[Sequence[Fr]]) -> Iterator[Fr]:
    """
    Perform inner product: state' = matrix * state
    """
    for row in range(len(state)):
        accumulation = Fr(0)
        for col, s in enumerate(state):
            accumulation += matrix[row][col] * s
        yield accumulation


def poseidon_hash(
    t: int,
    roundsF: int,
    roundsP: int,
    matrix: Sequence[Sequence[Fr]],
    constants: Sequence[Fr],
    inputs: Sequence[Fr],
) -> Fr:
    len_inputs = len(inputs)
    if len_inputs > t:
        raise ValueError(
            (
                "Length of inputs should be less than t."
                f"Got len(inputs): {len_inputs} "
                f"t: {t}"
            )
        )
    if len_inputs == 0:
        raise ValueError("Input shouldn't be empty")

    # Initial state is inputs padded with zeros to length t
    state = tuple(inputs) + (Fr(0),) * (t - len_inputs)

    halfF = roundsF / 2
    for i in range(roundsF + roundsP):
        state = ark(state, constants[i])
        if i < halfF or i >= halfF + roundsP:
            # Full S-Box layer round
            state = tuple(sigma(s) for s in state)
        else:
            # Partial S-Box layer round
            state = (sigma(state[0]),) + state[1:]
        state = mix(state, matrix)
    return state[0]
