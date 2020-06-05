from typing import Sequence


class Polynomial:
    coefficients: Sequence[int]

    def __init__(self, *args):
        self.coefficients = args

    def __repr__(self):
        return "".join(
            self.format_term(c_i, i) for i, c_i in enumerate(self.coefficients)
        )

    @staticmethod
    def format_term(coefficient, power):
        coefficient_part: str
        if coefficient == 0:
            return ""
        elif coefficient == 1:
            coefficient_part = " + "
        elif coefficient == -1:
            coefficient_part = " - "
        elif coefficient > 0:
            coefficient_part = f" + {coefficient}"
        else:
            coefficient_part = f" - {-coefficient}"
        if power == 0:
            return str(coefficient)
        elif power == 1:
            return f"{coefficient_part}x"
        else:
            return f"{coefficient_part}x^{power}"

    def evaluate(self, x):
        power = 1
        result = 0
        for coefficient in self.coefficients:
            result += coefficient * power
            power *= x
        return result
