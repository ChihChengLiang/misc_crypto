# fan-in   2 arithmetic circuits
# fan-out  n gates and m wires

from typing import Sequence
from .field import Field
from dataclasses import dataclass
from enum import Enum


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


class Opcode(Enum):
    ADD = 1
    MUL = 2
    EQ = 3
    SECRET_INPUT = 4
    PUBLIC_INPUT = 5

HANDLER_NAME = {
    Opcode.ADD: "add"
    Opcode.MUL: "mul"
    Opcode.EQ: "eq"
    Opcode.SECRET_INPUT: "secret_input"
    Opcode.PUBLIC_INPUT: "public_input"
}

@dataclass
class Selector:
    gate_left: Field
    gate_right: Field
    gate_output: Field
    gate_multiplication: Field
    gate_copy: Field

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
class Witness:
    a: Field
    b: Field
    c: Field

class Circuit:
    opcodes: Sequence[Opcode]


    def __init__(self):
        self.opcodes = []

    def add(self):
        self.opcodes.append(Opcode.ADD)
        return self

    def mul(self):
        self.opcodes.append(Opcode.MUL)
        return self

    def eq(self):
        self.opcodes.append(Opcode.EQ)
        return self

    def input(self, value):
        self.opcodes.append(Opcode.INPUT)
        self.opcodes.append(value)
        return self


def parse(instruction: Sequence[Opcode], machine):
    iterator = iter(instruction)
    try:
        next_item = next(iterator)
        if next_item == Opcode.ADD:
            machine.add()
        elif next_item == Opcode.MUL:
            machine.mul()
        elif next_item == Opcode.EQ:
            machine.eq()
        elif next_item == Opcode.INPUT:
            value = next(iterator)
            machine.input(value)
        else:
            raise Exception("Unreachable")
    except StopIteration:
        return

class Signal:
    name: str
    value: Field

    def __init__(self, name: str):
        self.name = name
        self.value = value

class WitnessMachine:
    a: Sequence[int]
    b: Sequence[int]
    c: Sequence[int]

    def __init__(self):
        self.a = []
        self.b = []
        self.c = []

    def private_signal(self, name:str):


    # def add(self):
    #     self.
    #     return self

    # def mul(self):
    #     self.opcodes.append(Opcode.MUL)
    #     return self

    # def eq(self):
    #     self.opcodes.append(Opcode.EQ)
    #     return self

    # def input(self, value):
    #     self.opcodes.append(Opcode.INPUT)
    #     self.opcodes.append(value)
    #     return self

def example_circuit():
    
    circuit = Circuit()
    x = circuit.secret_input("x")
    y = circuit.public_input("y")
    x.mul(x).mul(x).add(x).add(5).eq(y)

    return circuit

def check_circuit():
    circuit = example_circuit()
    circuit.calculate_witness(x= 3, y=35)

def gen_witness(x):
    a = [x,     x*x,    x*x*x,      35, x*x*x + x ]
    b = [x,     x,      x,          0,  5         ]
    c = [x*x,   x*x*x , x + x*x*x,  0,  35        ]
    return(a,b,c)

constraints = [Selector.mul(), Selector.mul(), Selector.add(),  Selector.input(35), Selector.add() ]

def copy_constraint(eval_domain, Xcoef, Ycoef, v1, v2):
    Px = [1]
    Y = []
    rlc = []
    x = []

    for i in range(0, len(eval_domain)):
        x.append(polynomial_eval(Xcoef, eval_domain[i]))
        Y.append(polynomial_eval(Ycoef, x[i]))

        rlc.append(v1 + x[i] + v2 * Y[i])
        Px.append(Px[i] * (v1 + x[i] + v2 * Y[i]))

    return (x, Y, Px, rlc)