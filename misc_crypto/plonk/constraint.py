# fan-in   2 arithmetic circuits
# fan-out  n gates and m wires

from typing import Sequence, Dict, Union, Tuple, NewType
from .field import FieldElement
from dataclasses import dataclass
from enum import Enum


WireIndex = NewType("WireIndex", int)


@dataclass
class ProverInput:
    witnesses: "GateVectors"
    selectors: Sequence["Selector"]
    public_inputs: Sequence[FieldElement]

    def number_of_gates(self):
        return len(self.witnesses.a)

    def get_public_input_evaluations(self):
        n = self.number_of_gates()
        n_public_inputs = len(self.public_inputs)
        return self.public_inputs + [0] * (n - n_public_inputs)


@dataclass
class GateVectors:
    # left
    a: Sequence[FieldElement]
    # right
    b: Sequence[FieldElement]
    # out
    c: Sequence[FieldElement]

    @classmethod
    def from_gates(cls, gates: Sequence["Gate"]):
        xa, xb, xc = [], [], []
        for gate in gates:
            a, b, c = gate.return_wire_value()
            xa.append(a)
            xb.append(b)
            xc.append(c)
        return cls(xa, xb, xc)


@dataclass
class GateWireVectors:
    a: Sequence[WireIndex]
    b: Sequence[WireIndex]
    c: Sequence[WireIndex]

    @classmethod
    def from_gates(cls, gates: Sequence["Gate"]):
        a, b, c = [], [], []
        for gate in gates:
            a_i, b_i, c_i = gate.return_wire_index()
            a.append(a_i)
            b.append(b_i)
            c.append(c_i)
        return cls(a, b, c)

    def concat(self):
        return self.a + self.b + self.c


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

    def return_wire_value(self):
        raise NotImplemented

    def return_wire_index(self):
        raise NotImplemented

    def get_selector(self):
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

    def return_wire_value(self):
        return self.left.value, self.right.value, self.out_wire.value

    def return_wire_index(self):
        return self.left.index, self.right.index, self.out_wire.index


class MulGate(TwoFanInGate):
    @classmethod
    def operate(cls, left_value, right_value):
        return left_value * right_value

    def get_selector(self):
        return Selector.mul()


class AddGate(TwoFanInGate):
    @classmethod
    def operate(cls, left_value, right_value):
        return left_value + right_value

    def get_selector(self):
        return Selector.add()


class VariableGate(Gate):
    name: str
    public: bool = False
    input_value = None
    # In wire is required by paper
    in_wire: "Wire"

    def feed_input(self, value):
        self.input_value = value

    def calculate_output(self,):
        return self.input_value

    def return_wire_value(self):
        return self.input_value, 0, self.out_wire.value

    def return_wire_index(self):
        if self.public:
            return self.in_wire.index, -1, self.out_wire.index
        else:
            return -1, -1, self.out_wire.index

    def get_selector(self):
        return Selector.input(self.input_value)


@dataclass
class Wire:
    in_gate: Gate = None
    out_gate: Gate = None
    index: WireIndex = -1
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

    def register_wire(self):
        wire = Wire()
        self.wires.append(wire)
        return wire

    def secret_input(self, name: str):
        gate = VariableGate()
        gate.name = name
        self.register_gate(gate)
        self.secret_inputs.append(gate)
        return gate

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
        gate.in_wire = self.register_wire()
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

        # Index wires
        wire_index = 0
        for variable in self.public_inputs:
            variable.in_wire.index = wire_index
            wire_index += 1
        for wire in self.wires:
            if wire.index == -1:
                wire.index = wire_index
                wire_index += 1

        # TODO: handle computational graph and stuff
        for gate in self.gates:
            gate.feed_output()

        selectors = []
        for gate in self.gates:
            selectors.append(gate.get_selector())
        gate_vector = GateVectors.from_gates(self.gates)

        public_inputs = [v.input_value for v in self.public_inputs]

        prover_input = ProverInput(
            witnesses=gate_vector, selectors=selectors, public_inputs=public_inputs
        )

        return prover_input

    def get_gate_wire_vector(self):
        gate_wire_vector = GateWireVectors.from_gates(self.gates)
        return gate_wire_vector

    def get_permutation(self):
        gate_wire_vector = self.get_gate_wire_vector().concat()
        len_vector = len(gate_wire_vector)
        mapping = {}
        for i, wire_index in enumerate(gate_wire_vector):
            if wire_index not in mapping:
                mapping[wire_index] = [i]
            else:
                mapping[wire_index].append(i)

        permutation_vector = list(range(len_vector))
        for wire_index, positions_in_vector in mapping.items():
            for i, position in enumerate(positions_in_vector):
                # Shift by one permutation
                permutation_vector[position] = positions_in_vector[i - 1]
        return permutation_vector


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
