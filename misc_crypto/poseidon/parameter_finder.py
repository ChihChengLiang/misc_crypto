# Adapt from Kobi's script
from math import log, ceil

M = 128  # bit security

# from py_ecc.bn128 import curve_order
# log(curve_order, 2)
n = 254

# interpolation
def check1(t, rf, rp):
    return rf + rp > log(2, 5) * min(n, M) + log(t, 2)


# grobner
def check2(rf, rp):
    return rf + rp > 0.21 * min(M, n)


def check3(t, rf, rp):
    return (t - 1) * rf + rp > 0.14 * min(M, n) - 1


def cost(t, rf, rp):
    return t * rf + rp


def find_parameter(t):
    minimal_rf = None
    minimal_rp = None

    for Rf in range(8, 10):
        for Rp in range(0, 200):
            if check1(t, Rf, Rp) and check2(Rf, Rp) and check3(t, Rf, Rp):
                c = cost(t, Rf, Rp)
                if (
                    minimal_rf is None
                    or minimal_rp is None
                    or c < cost(t, minimal_rf, minimal_rp)
                ):
                    minimal_rf = Rf
                    minimal_rp = Rp
                    print("Found new (Rf, Rp): (%d, %d), cost: %f" % (Rf, Rp, c))

    print(
        "Found minimal (Rf, Rp): (%d, %d), cost: %f, Rp with 7.5%% margin: %d"
        % (
            minimal_rf,
            minimal_rp,
            cost(t, minimal_rf, minimal_rp),
            ceil(1.075 * minimal_rp),
        )
    )
    return t, minimal_rf, minimal_rp


if __name__ == "__main__":
    for t in range(3, 31):
        _, minimal_rf, minimal_rp = find_parameter(t)
        print(t, minimal_rf, minimal_rp)
