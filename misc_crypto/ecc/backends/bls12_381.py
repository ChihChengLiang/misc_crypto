from typing import Any
from misc_crypto.ecc.protocol import FieldElement, IntOrFE, CurvePoint
from py_ecc.optimized_bls12_381 import (
    field_modulus,
    pairing,
    multiply,
    add,
    G1 as BLS12381G1,
    G2 as BLS12381G2,
    FQ,
    neg,
    double,
    eq,
    is_inf,
    curve_order,
    FQ12,
    final_exponentiate,
    Z1,
)


class Fr(FQ):
    field_modulus = curve_order


class WrappedCurvePoint:
    py_ecc_object: Any

    def __init__(self, py_ecc_object: Any):
        self.py_ecc_object = py_ecc_object

    def neg(self) -> "CurvePoint":
        return self.__class__(neg(self.py_ecc_object))

    def double(self) -> "CurvePoint":
        return self.__class__(double(self.py_ecc_object))

    def add(self, other: "CurvePoint") -> "CurvePoint":
        return self.__class__(add(self.py_ecc_object, other.py_ecc_object))

    def multiply(self, n: IntOrFE) -> "CurvePoint":
        return self.__class__(multiply(self.py_ecc_object, n))

    def eq(self, other: "CurvePoint") -> bool:
        return eq(self.py_ecc_object, other.py_ecc_object)

    def is_inf(self) -> bool:
        return is_inf(self.py_ecc_object)


class BLS12381Backend:
    curve_order = curve_order
    field_modulus = field_modulus

    @classmethod
    def Fq(cls) -> "FieldElement":
        return FQ

    @classmethod
    def Fr(cls) -> "FieldElement":
        return Fr

    @classmethod
    def G1(cls) -> "G1":
        return WrappedCurvePoint(BLS12381G1)

    @classmethod
    def Z1(cls) -> "G1":
        return WrappedCurvePoint(Z1)

    @classmethod
    def G2(cls) -> "G2":
        return WrappedCurvePoint(BLS12381G2)

    @classmethod
    def FQ12One(cls) -> "FQ12":
        return FQ12.one()

    @staticmethod
    def final_exponentiate(fq12: "FQ12") -> "FQ12":
        return final_exponentiate(fq12)

    @staticmethod
    def pairing(G1: "G1", G2: "G2", final_exponentiate: bool = True) -> bool:
        return pairing(G2.py_ecc_object, G1.py_ecc_object, final_exponentiate)
