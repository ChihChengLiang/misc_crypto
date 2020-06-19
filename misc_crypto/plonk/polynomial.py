from typing import Sequence, Union
from .field import FieldElement, roots_of_unity
from dataclasses import dataclass
from .fft import fft, inverse_fft
from .utils import next_power_of_2


@dataclass
class EvaluationDomain:
    domain: Sequence[FieldElement]

    @classmethod
    def from_roots_of_unity(cls, order: int):
        power_of_2_order = next_power_of_2(order)
        domain = roots_of_unity(power_of_2_order)
        return cls(domain)

    def inverse_fft(self, evaluations: Sequence[FieldElement]) -> "Polynomial":
        coefficients = inverse_fft(evaluations, self.domain)
        return Polynomial(*coefficients)


class Polynomial:
    """
    CoefficientForm
    """

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

    def add_polynomial(self, other: "Polynomial") -> "Polynomial":
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

    def add_scalar(self, other: FieldElement) -> "Polynomial":
        return Polynomial(self.coefficients[0] + other, *self.coefficients[1:])

    def shift(self, right: int) -> "Polynomial":
        if right == 0:
            return self
        elif right > 0:
            return Polynomial(*((0,) * right + self.coefficients))
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
        if isinstance(other, Polynomial):
            return self.add_polynomial(other)
        elif getattr(other, "__add__", None) is not None:
            return self.add_scalar(other)
        else:
            raise TypeError("invalid addition")

    def __sub__(self, other):
        if isinstance(other, Polynomial):
            return self.add_polynomial(-other)
        elif getattr(other, "__sub__", None) is not None:
            return self.add_scalar(-other)
        else:
            raise TypeError("invalid subtraction")

    def __neg__(self):
        return Polynomial(*[-c for c in self.coefficients])

    def multiply_constant(self, other: int) -> "Polynomial":
        return Polynomial(*(c * other for c in self.coefficients))

    def multiply_polynomial(self, other: "Polynomial") -> "Polynomial":
        result = Polynomial()
        for i, self_c in enumerate(self.coefficients):
            coeff = (0,) * i + tuple(self_c * other_c for other_c in other.coefficients)
            result = result.add_polynomial(Polynomial(*coeff))
        return result

    def __eq__(self, other: "Polynomial") -> bool:
        return self.coefficients == other.coefficients

    def satisfy(self, x: FieldElement) -> bool:
        return self.evaluate(x) == 0

    @property
    def is_zero(self) -> bool:
        return len(self.coefficients) == 0 or self.coefficients[0] == 0

    def __truediv__(self, other: "Polynomial") -> "Polynomial":
        if other.is_zero:
            raise ZeroDivisionError

        if self.degree < other.degree:
            raise ValueError("other has higher degree:", self, other)

        quotient = Polynomial(0)
        remainder = self
        for _ in range(self.degree - other.degree + 1):
            quotient_coefficient = remainder.coefficients[-1] / other.coefficients[-1]
            multiplier = Polynomial(quotient_coefficient).shift(
                remainder.degree - other.degree
            )
            quotient += multiplier
            remainder -= multiplier * other

        if not remainder.is_zero:
            raise ValueError("Remainder is not zero:", remainder)

        return quotient

    def fft(self, evaluation_domain: EvaluationDomain) -> Sequence[FieldElement]:
        evaluations = fft(self.coefficients, evaluation_domain.domain)
        return evaluations


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


def permutation_polynomial_evalutations(
    beta: FieldElement,
    gamma: FieldElement,
    f_evaluations: Sequence[FieldElement],
    s_id_evals: Sequence[FieldElement],
    s_sigma_evals: Sequence[int],
) -> Sequence[FieldElement]:
    """
    Returns evalutaions
    """
    z = [1]
    # We want z has same length as f_evaluations
    _zip = zip(f_evaluations[:-1], s_id_evals[:-1], s_sigma_evals[:-1])
    for f, s_id_eval, s_sigma_eval in _zip:
        f_prime = f + beta * s_id_eval + gamma
        g_prime = f + beta * s_sigma_eval + gamma
        product = z[-1] * f_prime / g_prime
        z.append(product)
    return z
