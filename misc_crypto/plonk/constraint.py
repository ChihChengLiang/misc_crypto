# fan-in   2 arithmetic circuits
# fan-out  n gates and m wires

from typing import Sequence, Dict, Union, Tuple, NewType
from .field import FieldElement
from dataclasses import dataclass
from enum import Enum
from math import log2, ceil


WireIndex = NewType("WireIndex", int)


def next_power_of_2(n: int) -> int:
    return 1 << ceil(log2(n))


@dataclass
class ProverInput:
    witnesses: "GateVectors"
    selectors: Sequence["Selector"]
    public_inputs: Sequence[FieldElement]
    public_input_evaluations: Sequence[FieldElement]
    permutation: Sequence[int]

    def number_of_gates(self):
        return len(self.witnesses.a)

    def get_public_input_evaluations(self):
        """
        We use negative pi in prover. See paper p.24
        """
        return [-pi for pi in self.public_input_evaluations]

    def flatten_selectors(self):
        qm, ql, qr, qo, qc = [], [], [], [], []
        for s in self.selectors:
            qm.append(s.gate_multiplication)
            ql.append(s.gate_left)
            qr.append(s.gate_right)
            qo.append(s.gate_output)
            qc.append(s.gate_copy)
        return qm, ql, qr, qo, qc

    def split_permutations(self):
        n = self.number_of_gates()
        s_sigma_1 = self.permutation[:n]
        s_sigma_2 = self.permutation[n : 2 * n]
        s_sigma_3 = self.permutation[2 * n :]
        return s_sigma_1, s_sigma_2, s_sigma_3

    def split_witnesses(self):
        return self.witnesses.a, self.witnesses.b, self.witnesses.c


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
        return cls(1, 1, -1, 0, 0)

    @classmethod
    def mul(cls):
        return cls(0, 0, -1, 1, 0)

    @classmethod
    def eq(cls):
        return cls(-1, 0, 0, 1, 0)

    @classmethod
    def input(cls):
        return cls(1, 0, 0, 0, 0)

    @classmethod
    def dummy(cls):
        return cls(0, 0, 0, 0, 0)


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


class PublicInputGate(Gate):
    in_wire: "Wire"

    def calculate_output(self,):
        return self.in_wire.value

    def return_wire_value(self):
        return self.in_wire.value, 0, self.out_wire.value

    def return_wire_index(self):
        return self.in_wire.index, -1, self.out_wire.index

    def get_selector(self):
        return Selector.input()


class DummyGate(Gate):
    """
    We pad this gate to make the number of gates to be power of 2,
    which is required by fft.
    """

    def feed_output(self):
        pass

    def calculate_output(self,):
        return 0

    def return_wire_value(self):
        return 0, 0, 0

    def return_wire_index(self):
        return -1, -1, -1

    def get_selector(self):
        return Selector.dummy()


@dataclass
class Variable:
    name: str
    public: bool = False
    input_value = None

    def feed_input(self, value):
        self.input_value = value


@dataclass
class Wire:
    intake: Union[Gate, Variable] = None
    out_gate: Gate = None
    index: WireIndex = -1
    value = None


class Circuit:
    secret_inputs: Sequence[Variable]
    wires: Sequence[Wire]
    gates: Sequence[Gate]
    public_inputs: Sequence[Variable]

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
        variable = Variable(name=name, public=False)
        wire = self.register_wire()
        wire.intake = variable
        self.secret_inputs.append(variable)
        return wire

    def gate_or_wire(self, gate_or_wire: Union[Gate, Wire]) -> Wire:
        if isinstance(gate_or_wire, Gate):
            return gate_or_wire.out_wire
        elif isinstance(gate_or_wire, Wire):
            return gate_or_wire
        else:
            raise Exception("Unreachable")

    def gate_mul(self, left: Union[Gate, Wire], right: Union[Gate, Wire]):
        left_wire = self.gate_or_wire(left)
        right_wire = self.gate_or_wire(right)
        gate = MulGate(left_wire, right_wire)
        left_wire.out_gate = gate
        right_wire.out_gate = gate
        self.register_gate(gate)
        return gate

    def gate_add(self, left: Union[Gate, Wire], right: Union[Gate, Wire]):
        left_wire = self.gate_or_wire(left)
        right_wire = self.gate_or_wire(right)
        gate = AddGate(left_wire, right_wire)
        left_wire.out_gate = gate
        right_wire.out_gate = gate
        self.register_gate(gate)
        return gate

    def gate_public_input(self, name: str):
        """
        Public input needs a wire and a gate (required by the paper)

        """
        variable = Variable(name=name, public=True)
        gate = PublicInputGate()
        wire = self.register_wire()
        wire.intake = variable
        wire.out_gate = gate
        gate.in_wire = wire
        self.public_inputs.append(variable)
        self.register_gate(gate)
        return gate

    def output_eq(self, gate1: Gate, gate2: Gate):
        wire = self.register_wire()
        wire.intake = gate1
        wire.out_gate = gate2

    def num_non_trivial_gates(self):
        return len([gate for gate in self.gates if not isinstance(gate, DummyGate)])

    def calculate_witness(self, input_mapping):
        len_gate = len(self.gates)
        dummy_gates_to_add = next_power_of_2(len_gate) - len_gate
        for _ in range(dummy_gates_to_add):
            self.gates.append(DummyGate())

        for variable in self.public_inputs + self.secret_inputs:
            variable.feed_input(input_mapping[variable.name])

        # Index wires
        wire_index = 0
        for wire in self.wires:
            if wire.index == -1:
                wire.index = wire_index
                wire_index += 1

        # TODO: handle computational graph and stuff
        for wire in self.wires:
            if isinstance(wire.intake, Variable):
                wire.value = wire.intake.input_value
        for gate in self.gates:
            gate.feed_output()

    def get_gate_vector(self):
        return GateVectors.from_gates(self.gates)

    def get_gate_wire_vector(self):
        return GateWireVectors.from_gates(self.gates)

    def get_selectors(self):
        selectors = []
        for gate in self.gates:
            selectors.append(gate.get_selector())
        return selectors

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

    def get_prover_input(self):
        gate_vector = self.get_gate_vector()
        selectors = self.get_selectors()

        public_inputs = [v.input_value for v in self.public_inputs]

        public_input_evaluations = []

        for gate in self.gates:
            public_input_evaluations.append(
                gate.calculate_output() if isinstance(gate, PublicInputGate) else 0
            )
        print(public_input_evaluations)

        permutation = self.get_permutation()

        prover_input = ProverInput(
            witnesses=gate_vector,
            selectors=selectors,
            public_inputs=public_inputs,
            public_input_evaluations=public_input_evaluations,
            permutation=permutation,
        )

        return prover_input


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
