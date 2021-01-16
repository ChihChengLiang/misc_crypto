from typing import Protocol, Union, TypeVar, Type


T = TypeVar("T", bound="FieldElement")

IntOrFE = Union[int, T]


class FieldElement(Protocol):
    field_modulus: int

    def __add__(self: T, other: IntOrFE) -> T:
        ...

    def __mul__(self: T, other: IntOrFE) -> T:
        ...

    def __sub__(self: T, other: IntOrFE) -> T:
        ...

    def __div__(self: T, other: IntOrFE) -> T:
        ...

    def __rmul__(self: T, other: IntOrFE) -> T:
        ...

    def __radd__(self: T, other: IntOrFE) -> T:
        ...

    def __rsub__(self: T, other: IntOrFE) -> T:
        ...

    def __pow__(self: T, other: int) -> T:
        ...

    def __neg__(self: T) -> T:
        ...

    def __int__(self: T) -> int:
        ...

    @classmethod
    def one(cls: Type[T]) -> T:
        ...

    @classmethod
    def zero(cls: Type[T]) -> T:
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
    def Fq(cls, n: int) -> "FieldElement":
        ...

    @classmethod
    def Fr(cls, n: int) -> "FieldElement":
        ...

    @classmethod
    def get_G1(cls) -> "G1":
        ...

    @classmethod
    def get_G2(cls) -> "G2":
        ...

    @classmethod
    def Z1(cls) -> "G1":
        ...

    def FQ12One(cls) -> "FQ12":
        ...

    @staticmethod
    def final_exponentiate(fq12: "FQ12") -> "FQ12":
        ...

    @staticmethod
    def pairing(G1: "G1", G2: "G2", final_exponentiate: bool = True) -> "FQ12":
        ...
