from typing import Any
from misc_crypto.ecc.protocol import FieldElement, IntOrFE
from py_ecc.optimized_bn128 import (
    field_modulus,
    pairing,
    multiply,
    add,
    G1 as BN254G1,
    G2 as BN254G2,
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

    def neg(self) -> "WrappedCurvePoint":
        return self.__class__(neg(self.py_ecc_object))

    def double(self) -> "WrappedCurvePoint":
        return self.__class__(double(self.py_ecc_object))

    def add(self, other: "WrappedCurvePoint") -> "WrappedCurvePoint":
        return self.__class__(add(self.py_ecc_object, other.py_ecc_object))

    def multiply(self, n: IntOrFE) -> "WrappedCurvePoint":
        return self.__class__(multiply(self.py_ecc_object, int(n)))

    def eq(self, other: "WrappedCurvePoint") -> bool:
        return eq(self.py_ecc_object, other.py_ecc_object)

    def is_inf(self) -> bool:
        return is_inf(self.py_ecc_object)


class G1(WrappedCurvePoint):
    ...


class G2(WrappedCurvePoint):
    ...


class BN254Backend:
    curve_order = curve_order
    field_modulus = field_modulus

    @classmethod
    def Fq(cls, n: IntOrFE) -> "FieldElement":
        return FQ(n)

    @classmethod
    def Fr(cls, n: IntOrFE) -> "FieldElement":
        return Fr(n)

    @classmethod
    def get_G1(cls) -> G1:
        return G1(BN254G1)

    @classmethod
    def Z1(cls) -> G1:
        return G1(Z1)

    @classmethod
    def get_G2(cls) -> G2:
        return G2(BN254G2)

    @classmethod
    def FQ12One(cls) -> "FQ12":
        return FQ12.one()

    @staticmethod
    def final_exponentiate(fq12: "FQ12") -> "FQ12":
        return final_exponentiate(fq12)

    @staticmethod
    def pairing(G1: "G1", G2: "G2", final_exponentiate: bool = True) -> "FQ12":
        return pairing(G2.py_ecc_object, G1.py_ecc_object, final_exponentiate)
