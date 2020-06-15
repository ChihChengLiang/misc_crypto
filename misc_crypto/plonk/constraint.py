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
    index: int = -1
    out_wire: "Wire" = None

    def feed_output(self):
        calculated_output = self.calculate_output()
        if self.out_wire.value != None:
            raise ValueError(
                f"Contradiction, outwire has value {self.out_wire.value}, but this gate is feeding it {calculated_output}"
            )
        else:
            self.out_wire.value = calculated_output

    def calculate_output(self):
        raise NotImplemented

    def return_abc_value(self):
        raise NotImplemented


class TwoFanInGate(Gate):
    left: "Wire"
    right: "Wire"

    def __init__(self, left, right, **kwargs):
        super().__init__(**kwargs)
        self.left = left
        self.right = right

    @classmethod
    def operate(cls, left_value, right_value):
        raise NotImplemented

    def calculate_output(self):
        return self.operate(self.left.value, self.right.value)

    def return_abc_value(self):
        return self.left.value, self.right.value, self.out_wire.value


class MulGate(TwoFanInGate):
    @classmethod
    def operate(cls, left_value, right_value):
        return left_value * right_value


class AddGate(TwoFanInGate):
    @classmethod
    def operate(cls, left_value, right_value):
        return left_value + right_value


class VariableGate(Gate):
    name: str
    public: bool = False
    input_value = None

    def feed_input(self, value):
        self.input_value = value

    def calculate_output(self,):
        return self.input_value

    def return_abc_value(self):
        return self.input_value, 0, self.out_wire.value


@dataclass
class Wire:
    in_gate: Gate = None
    out_gate: Gate = None
    index: int = -1
    value = None


class Circuit:
    secret_inputs: Sequence[VariableGate]
    wires: Sequence[Wire]
    gates: Sequence[Gate]
    public_inputs: Sequence[VariableGate]

    def __init__(self):
        self.wires = []
        self.secret_inputs = []
        self.gates = []
        self.public_inputs = []

    def print(self):
        print()
        for g in self.gates:
            print(g)

        for wire in self.wires:
            print(wire)

    def register_gate(self, gate: Gate):
        out_wire = self.register_wire()
        gate.out_wire = out_wire
        out_wire.out_gate = gate
        self.gates.append(gate)
        return gate

    def secret_input(self, name: str):
        gate = VariableGate()
        gate.name = name
        self.register_gate(gate)
        self.secret_inputs.append(gate)
        return gate

    def register_wire(self):
        wire = Wire()
        self.wires.append(wire)
        return wire

    def gate_mul(self, left: Gate, right: Gate):
        gate = MulGate(left.out_wire, right.out_wire)
        self.register_gate(gate)
        return gate

    def gate_add(self, left: Gate, right: Gate):
        gate = AddGate(left.out_wire, right.out_wire)
        self.register_gate(gate)
        return gate

    def gate_public_input(self, name: str):
        gate = VariableGate()
        gate.name = name
        gate.public = True
        print(gate)
        self.public_inputs.append(gate)
        self.register_gate(gate)
        return gate

    def output_eq(self, gate1: Gate, gate2: Gate):
        wire = self.register_wire()
        wire.in_gate = gate1
        wire.out_gate = gate2

    def calculate_witness(self, input_mapping):

        for variable in self.public_inputs + self.secret_inputs:
            variable.feed_input(input_mapping[variable.name])
        # TODO: handle computational graph and stuff
        for gate in self.gates:
            gate.feed_output()

        va = []
        vb = []
        vc = []
        for gate in self.gates:
            a, b, c = gate.return_abc_value()
            va.append(a)
            vb.append(b)
            vc.append(c)
        return va, vb, vc


def circuit():

    c = Circuit()
    x = c.secret_input("x")
    x2 = c.gate_mul(x, x)
    x3 = c.gate_mul(x2, x)
    x3_plus_x = c.gate_add(x, x3)
    constant = c.gate_public_input("const")
    x3_plus_x_plus_const = c.gate_add(x3_plus_x, constant)
    y = c.gate_public_input("y")
    c.output_eq(x3_plus_x_plus_const, y)
    return c
