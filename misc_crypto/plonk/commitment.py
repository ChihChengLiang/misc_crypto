from .field import G1
from typing import Sequence

class Commitment:
    value: G1


# Proof that a polynomial `p` was correctly evaluated at a point `z`
class Proof:
    commitment_to_witness: "Commitment"
    evaluated_point: "G1"
    commitment_to_polynomial: "Commitment"

class AggregateProof:
    commitment_to_witness: "Commitment"
    evaluated_points: Sequence["G1"]
    commitment_to_polynomial: "Commitment"

    def flatten(self) -> "Proof":
        pass