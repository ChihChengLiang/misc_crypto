from math import log2, ceil

def is_power_of_2(n: int) -> bool:
    return (n & (n - 1) == 0) and n != 0


def next_power_of_2(n: int) -> int:
    return 1 << ceil(log2(n))