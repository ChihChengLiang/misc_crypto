from py_ecc.bn128 import curve_order
from py_ecc.fields import FQ


# All the algebra of the circuit must be in the Fr Field
class Fr(FQ):
    field_modulus = curve_order
