from typing import Protocol, Union

IntOrFE = Union[int, "FieldElement"]


class FieldElement(Protocol):
    def __add__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __mul__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __sub__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __div__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __rmul__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __radd__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __rsub__(self, other: IntOrFE) -> "FieldElement":
        ...

    def __pow__(self, other: int) -> "FieldElement":
        ...

    def __neg__(self) -> "FieldElement":
        ...

    @classmethod
    def one(cls) -> "FieldElement":
        ...

    @classmethod
    def zero(cls) -> "FieldElement":
        ...


class FQ12(FieldElement):
    ...


class CurvePoint(Protocol):
    def neg(self) -> "CurvePoint":
        ...

    def double(self) -> "CurvePoint":
        ...

    def add(self, other: "CurvePoint") -> "CurvePoint":
        ...

    def multiply(self, n: IntOrFE) -> "CurvePoint":
        ...

    def eq(self, other: "CurvePoint") -> bool:
        ...

    def is_inf(self) -> bool:
        ...


class G1(CurvePoint):
    ...


class G2(CurvePoint):
    ...


class Backend(Protocol):
    curve_order: int
    field_modulus: int

    @classmethod
    def Fq(cls) -> "FieldElement":
        ...

    @classmethod
    def Fr(cls) -> "FieldElement":
        ...

    @classmethod
    def G1(cls) -> "G1":
        ...

    @classmethod
    def G2(cls) -> "G2":
        ...

    @classmethod
    def Z1(cls) -> "G1":
        ...

    @staticmethod
    def final_exponentiate(fq12: "FQ12") -> "FQ12":
        ...

    @staticmethod
    def pairing(G1: "G1", G2: "G2", final_exponentiate: bool = True) -> bool:
        ...
