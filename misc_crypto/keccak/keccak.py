from typing import List, Sequence


ROUNDS = 24

# rotation offsets
ROT = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]

ROUND_CONSTANTS = [
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
]

# width b is 1600 bits
WIDTH_BYTES = 200
DIGEST_BYTES = 32
# capacity c is 512 bits, which is the double of the digest 256 bits
# See https://github.com/Legrandin/pycryptodome/blob/master/lib/Crypto/Hash/keccak.py#L73
CAPACITY_BYTES = 64
# bitrate rate r = b - c is 1088 bits
RATE_BYTES = WIDTH_BYTES - CAPACITY_BYTES

# https://github.com/Legrandin/pycryptodome/blob/5dace638b70ac35bb5d9b565f3e75f7869c9d851/lib/Crypto/Hash/keccak.py#L74
DELIMITED_SUFFIX = 0x01


def keccak_f(lanes: List[List[int]]) -> List[List[int]]:
    a = lanes
    for round_constant in ROUND_CONSTANTS:
        a = round_f(a, round_constant)
    return a


def rotate_left(x: int, y: int) -> int:
    """
    bitwise cyclic shift left operation
    cyclic shift the input x y bits left
    """
    return ((x << y) | (x >> (64 - y))) % (1 << 64)


def round_f(a: List[List[int]], round_constant: int) -> List[List[int]]:
    assert type(a) == list
    assert type(a[0][0]) == int
    # Theta step
    c = [a[x][0] ^ a[x][1] ^ a[x][2] ^ a[x][3] ^ a[x][4] for x in range(5)]

    d = [c[x - 1] ^ rotate_left(c[(x + 1) % 5], 1) for x in range(5)]
    for x in range(5):
        for y in range(5):
            a[x][y] ^= d[x]

    # Rho + Pi steps
    b = [[0 for x in range(5)] for y in range(5)]
    for x in range(5):
        for y in range(5):
            b[y][(2 * x + 3 * y) % 5] = rotate_left(a[x][y], ROT[x][y])
    # Xi step
    for x in range(5):
        for y in range(5):
            a[x][y] = b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y])
    # Iota step
    a[0][0] ^= round_constant
    return a


def load64(b: Sequence[int]) -> int:
    return sum((b[i] << (8 * i)) for i in range(8))


def store64(a: int) -> List[int]:
    return [(a >> (8 * i)) % 256 for i in range(8)]


def keccak_f1600(state: bytearray) -> bytearray:
    lanes = [
        [load64(state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8]) for y in range(5)]
        for x in range(5)
    ]
    lanes = keccak_f(lanes)
    state = bytearray(200)
    for x in range(5):
        for y in range(5):
            state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8] = store64(lanes[x][y])
    return state


def sponge_absorb(state: bytearray, input_bytes: bytes) -> bytearray:
    offset = 0
    block_size = 0
    length = len(input_bytes)
    while offset < length:
        block_size = min(length - offset, RATE_BYTES)
        for i in range(block_size):
            state[i] ^= input_bytes[i + offset]
        offset += block_size
        if block_size == RATE_BYTES:
            state = keccak_f1600(state)
            block_size = 0
    # Padding
    state[block_size] ^= DELIMITED_SUFFIX
    if DELIMITED_SUFFIX & 0x80 != 0 and block_size == RATE_BYTES - 1:
        state = keccak_f1600(state)
    state[RATE_BYTES - 1] ^= 0x80
    state = keccak_f1600(state)

    return state


def sponge_squeeze(state: bytearray) -> bytes:
    output_bytes = bytearray()
    length = DIGEST_BYTES
    while length > 0:
        block_size = min(length, RATE_BYTES)
        output_bytes += state[0:block_size]
        length -= block_size
        if length > 0:
            state = keccak_f1600(state)
    return bytes(output_bytes)


def keccak_256(input_bytes: bytes) -> bytes:
    state = bytearray([0 for _ in range(WIDTH_BYTES)])
    state = sponge_absorb(state, input_bytes)
    output_bytes = sponge_squeeze(state)
    return output_bytes


def test_keccak():
    _input = "abcde".encode("utf8")
    from eth_hash.auto import keccak
    from random import randbytes, randint

    assert keccak_256(b"") == keccak(b"")
    assert keccak_256(_input) == keccak(_input)

    for _ in range(100):
        n = randint(0, 600)
        _input = randbytes(n)
        assert keccak_256(_input) == keccak(_input)
