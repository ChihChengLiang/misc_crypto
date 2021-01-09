from typing import Sequence


def s_id(j: int, n: int, i: int, domain):
    return domain.fft((j - 1) * n + i)


def s_sigma(j: int, n: int, i: int, permutation: Sequence[int]):
    return permutation[(j - 1) * n + i]
