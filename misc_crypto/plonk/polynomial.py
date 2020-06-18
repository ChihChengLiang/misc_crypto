from typing import Sequence, Union
from .field import FieldElement, roots_of_unity
from dataclasses import dataclass


def fft(
    coefficients: Sequence[FieldElement], domain: Sequence[FieldElement]
) -> Sequence[FieldElement]:
    # TODO: Check domain to be power of 2
    if len(coefficients) == 1:
        return coefficients
    evens = fft(coefficients[::2], domain[::2])
    odds = fft(coefficients[1::2], domain[::2])
    left_output = []
    right_output = []
    for even, odd, x in zip(evens, odds, domain):
        x_odd = x * odd
        left_output.append(even + x_odd)
        right_output.append(even - x_odd)
    return left_output + right_output


def inverse_fft(
    evaluations: Sequence[FieldElement], domain: Sequence[FieldElement]
) -> Sequence[FieldElement]:
    values = fft(evaluations, domain)
    # TODO: len_values should be mod field modulus. The function breaks in small field
    len_values = len(values)
    return [v / len_values for v in [values[0]] + values[1:][::-1]]


@dataclass
class EvaluationDomain:
    domain: Sequence[FieldElement]

    @classmethod
    def from_roots_of_unity(cls, order: int):
        domain = roots_of_unity(order)
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

        if len(other.coefficients) > 2 or other.coefficients[1] != 1:
            raise NotImplementedError("General polynomial division is unsupported")

        q = Polynomial(0)
        r = self
        while not r.is_zero and r.degree >= other.degree:
            t = Polynomial(r.coefficients[-1]).shift(r.degree - other.degree)
            q = q + t
            r = r - t * other

        if not r.is_zero:
            raise ValueError("Remainder is not zero:", r)

        return q

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
    for f, s_id_eval, s_sigma_eval in zip(f_evaluations, s_id_evals, s_sigma_evals):
        f_prime = f + beta * s_id_eval + gamma
        g_prime = f + beta * s_sigma_eval + gamma
        product = z[-1] * f_prime / g_prime
        z.append(product)
    return z
