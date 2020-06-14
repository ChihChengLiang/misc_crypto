# fan-in   2 arithmetic circuits
# fan-out  n gates and m wires

from typing import Sequence, Dict, Union, Tuple
from .field import FieldElement
from dataclasses import dataclass
from enum import Enum


@dataclass
class Selector:
    gate_left: FieldElement
    gate_right: FieldElement
    gate_output: FieldElement
    gate_multiplication: FieldElement
    gate_copy: FieldElement

    @classmethod
    def add(cls):
        return cls(1, 1, 0, -1, 0)

    @classmethod
    def mul(cls):
        return cls(0, 0, 1, -1, 0)

    @classmethod
    def eq(cls):
        return cls(-1, 0, 1, 0, 0)

    @classmethod
    def input(cls, value):
        return cls(1, 0, 0, 0, -value)


@dataclass
class Gate:
    index: int
    left: "Wire"
    right: "Wire"
    out: "Wire"

    def __repr__(self):
        left_index = self.left.index if self.left is not None else None
        right_index = self.right.index if self.right is not None else None
        out_index = self.out.index if self.out is not None else None
        return (
            f"<Gate {self.index} left {left_index} right {right_index} out {out_index}>"
        )


@dataclass
class Wire:
    index: int
    name: None
    hand: Gate
    other_hand: Gate

    def __repr__(self):
        hand_index = self.hand.index if self.hand is not None else None
        other_hand_index = (
            self.other_hand.index if self.other_hand is not None else None
        )

        return f"<Wire {self.index} name {self.name} hand {hand_index} other_hand {other_hand_index}>"


class Circuit:
    secret_inputs: Dict[str, Wire]
    wires: Sequence[Wire]
    gates: Sequence[Gate]
    public_inputs: Sequence[Wire]
    selectors: Sequence[Selector]

    def __init__(self):
        self.wires = []
        self.secret_inputs = []
        self.gates = []
        self.public_inputs = []
        self.selectors = []

    def print(self):
        print()
        for g in self.gates:
            print(g)

        for wire in self.wires:
            print(wire)

    def secret_input(self, name: str):
        gate = self.new_gate(left=None, right=None)
        self.secret_inputs.append(gate)
        return gate

    def new_wire(self, name: str = None, hand=None, other_hand=None):
        index = len(self.wires)
        wire = Wire(index=index, name=name, hand=hand, other_hand=other_hand)
        self.wires.append(wire)
        return wire

    def new_gate_from_wire(self, left: Wire, right: Wire):
        gate_index = len(self.gates)
        out_wire = self.new_wire()
        gate = Gate(index=gate_index, left=left, right=right, out=out_wire)
        out_wire.hand = gate
        self.gates.append(gate)
        return gate

    def new_gate(self, left: Gate, right: Gate):
        left_wire = left.out if left is not None else None
        right_wire = right.out if right is not None else None
        gate = self.new_gate_from_wire(left_wire, right_wire)
        if left is not None:
            left_wire.other_hand = gate
        if right is not None:
            right_wire.other_hand = gate
        return gate

    def gate_mul(self, left: Gate, right: Gate):
        self.selectors.append(Selector.mul())
        gate = self.new_gate(left, right)
        return gate

    def gate_add(self, left: Wire, right: Wire):
        self.selectors.append(Selector.add())
        gate = self.new_gate(left, right)
        return gate

    def gate_public_input(self, name: str):
        # self.selectors.append(Selector.input())
        wire = self.new_wire(name)
        self.public_inputs.append(wire)
        gate = self.new_gate_from_wire(left=wire, right=None)
        return gate

    def output_eq(self, gate1: Gate, gate2: Gate):
        self.new_wire(hand=gate1.out, other_hand=gate2.out)


def circuit():

    c = Circuit()
    x = c.secret_input("x")
    g1 = c.gate_mul(x, x)
    g2 = c.gate_mul(g1, x)
    g3 = c.gate_add(x, g2)
    g4 = c.gate_public_input("const")
    g5 = c.gate_add(g4, g3)
    g6 = c.gate_public_input("y")
    c.output_eq(g5, g6)
    return c
