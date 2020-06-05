# fan-in   2 arithmetic circuits
# fan-out  n gates and m wires

from typing import Sequence
from .field import Field


class Vabc:
    a: Sequence[int]  # [m]^n left
    b: Sequence[int]  # right
    c: Sequence[int]  # output


class SelectorVectors:
    q_l: Sequence[Field]
    q_r: Sequence[Field]
    q_o: Sequence[Field]
    q_m: Sequence[Field]
    q_c: Sequence[Field]


class ConstraintSystem:
    V: Vabc
    Q: SelectorVectors
