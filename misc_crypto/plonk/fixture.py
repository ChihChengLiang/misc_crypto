def gen_witness(x):
    """
    x^3 + x + 35
    """
    a = [x, x * x, x * x * x, 1, 1, x * x * x + x]
    b = [x, x, x, 5, 35, 5]
    c = [x * x, x * x * x, x + x * x * x, 5, 35, 35]
    return a, b, c
