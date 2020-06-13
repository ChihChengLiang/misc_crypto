from typing import Sequence, Union
from .field import FieldElement


class Polynomial:
    coefficients: Sequence[FieldElement]

    def __init__(self, *args):
        self.coefficients = args
        self.remove_leading_zeros()

    @classmethod
    def from_roots(cls, *roots):
        result = cls(1)
        for root in roots:
            result *= cls(-root, 1)
        return result

    def __repr__(self):
        terms = "".join(
            self.format_term(c_i, i) for i, c_i in enumerate(self.coefficients)
        )
        return f"Polynomial<{terms}>"

    @staticmethod
    def format_term(coefficient, power):
        coefficient_part: str
        if coefficient == 0:
            return ""
        elif coefficient == 1:
            coefficient_part = " + "
        elif coefficient == -1:
            coefficient_part = " - "
        elif isinstance(coefficient, int) and coefficient < 0:
            coefficient_part = f" - {-coefficient}"
        else:
            coefficient_part = f" + {coefficient}"
        if power == 0:
            return str(coefficient)
        elif power == 1:
            return f"{coefficient_part}x"
        else:
            return f"{coefficient_part}x^{power}"

    def evaluate(self, x: FieldElement) -> FieldElement:
        power = 1
        result = 0
        for coefficient in self.coefficients:
            result += coefficient * power
            power *= x
        return result

    def remove_leading_zeros(self) -> None:
        while len(self.coefficients) > 0 and self.coefficients[-1] == 0:
            self.coefficients = self.coefficients[:-1]

    @property
    def degree(self) -> int:
        return len(self.coefficients)

    def add(self, other: "Polynomial") -> "Polynomial":
        long_poly, short_poly = (
            (self, other) if self.degree >= other.degree else (other, self)
        )
        min_degree = min(self.degree, other.degree)
        coefficients = (
            tuple(
                l + s for l, s in zip(long_poly.coefficients, short_poly.coefficients)
            )
            + long_poly.coefficients[min_degree:]
        )
        return Polynomial(*coefficients)

    def shift(self, right: int) -> "Polynomial":
        if right == 0:
            return self
        elif right > 0:
            return Polynomial(*([0] * len(right) + self.coefficients))
        elif right < 0:
            raise ValueError("shift left not supported yet")
        else:
            raise Exception("Unreachable")

    def __mul__(self, other: Union["Polynomial", FieldElement]) -> "Polynomial":
        if isinstance(other, Polynomial):
            return self.multiply_polynomial(other)
        elif getattr(other, "__mul__", None) is not None:
            return self.multiply_constant(other)
        else:
            raise TypeError("invalid multiplication")

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return Polynomial(
                *((self.coefficients[0] + other,) + self.coefficients[0:])
            )
        elif isinstance(other, Polynomial):
            return self.add(other)
        else:
            raise TypeError("invalid multiplication")

    def multiply_constant(self, other: int) -> "Polynomial":
        return Polynomial(*(c * other for c in self.coefficients))

    def multiply_polynomial(self, other: "Polynomial") -> "Polynomial":
        result = Polynomial()
        for i, self_c in enumerate(self.coefficients):
            coeff = (0,) * i + tuple(self_c * other_c for other_c in other.coefficients)
            result = result.add(Polynomial(*coeff))
        return result

    def __eq__(self, other: "Polynomial") -> bool:
        return self.coefficients == other.coefficients

    def satisfy(self, x: FieldElement) -> bool:
        return self.evaluate(x) == 0


def lagrange(x: Sequence[FieldElement], y: Sequence[FieldElement]) -> Polynomial:
    if len(x) != len(y):
        raise ValueError("length should not be different")
    result = Polynomial()
    for i in range(len(x)):
        x_rest = x[:i] + x[i + 1 :]
        denominator = 1
        for xx in x_rest:
            denominator *= x[i] - xx
        coeff = y[i] / denominator
        result += Polynomial.from_roots(*x_rest) * coeff
    return result


def coordinate_pair_accumulator(
    x: Polynomial, y: Polynomial, n: int, v1, v2
) -> Polynomial:
    p = [1]
    evaluation_domain = list(range(n))
    for i in evaluation_domain:
        p.append(p[-1] * (v1 + x.evaluate(i) + v2 * y.evaluate(i)))
    return lagrange(evaluation_domain, p[:-1])
