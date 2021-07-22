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


def keccak_function(lanes: Sequence[Sequence[int]]) -> List[List[int]]:
    a = lanes
    for round_constant in ROUND_CONSTANTS:
        a = round(a, round_constant)
    return a


def rol64(x: int, y: int) -> int:
    """
    bitwise cyclic shift operation
    """
    return ((x << y) | (x >> (64 - y))) % (1 << 64)


def round(a: Sequence[Sequence[int]], round_constant: int) -> List[List[int]]:
    assert type(a) == list
    assert type(a[0][0]) == int
    # Theta step
    c = [a[x][0] ^ a[x][1] ^ a[x][2] ^ a[x][3] ^ a[x][4] for x in range(5)]

    d = [c[x - 1] ^ rol64(c[(x + 1) % 5], 1) for x in range(5)]
    for x in range(5):
        for y in range(5):
            a[x][y] ^= d[x]

    # Rho + Pi steps
    b = [[0 for x in range(5)] for y in range(5)]
    for x in range(5):
        for y in range(5):
            b[y][(2 * x + 3 * y) % 5] = rol64(a[x][y], ROT[x][y])
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


def keccak_f1600(state: Sequence[Sequence[int]]) -> List[List[int]]:
    lanes = [
        [load64(state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8]) for y in range(5)]
        for x in range(5)
    ]
    lanes = keccak_function(lanes)
    state = bytearray(200)
    for x in range(5):
        for y in range(5):
            state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8] = store64(lanes[x][y])
    return state


def keccak_full(
    rate: int,
    capacity: int,
    input_bytes: Sequence[bytes],
    delimited_suffix: bytes,
    output_byte_len: int,
) -> bytearray:
    """
    from https://github.com/XKCP/XKCP/blob/master/Standalone/CompactFIPS202/Python/CompactFIPS202.py
    """
    assert rate + capacity == 1600
    assert rate % 8 == 0
    block_size = 0
    input_offset = 0
    rate_in_bytes = rate // 8
    output_bytes = []
    state = bytearray([0 for i in range(200)])
    input_offset = 0
    # Absorb
    while input_offset < len(input_bytes):
        block_size = min(len(input_bytes) - input_offset, rate_in_bytes)
        for i in range(block_size):
            state[i] ^= input_bytes[i + input_offset]
        input_offset += block_size
        if block_size == rate_in_bytes:
            state = keccak_f1600(state)
            block_size = 0
    # Padding
    state[block_size] ^= delimited_suffix
    if delimited_suffix & 0x80 != 0 and block_size == rate_in_bytes - 1:
        state = keccak_f1600(state)
    state[rate_in_bytes - 1] ^= 0x80
    state = keccak_f1600(state)
    # Squeeze
    while output_byte_len > 0:
        block_size = min(output_byte_len, rate_in_bytes)
        output_bytes += state[0:block_size]
        output_byte_len -= block_size
        if output_byte_len > 0:
            state = keccak_f1600(state)
    return bytearray(output_bytes)


def keccak_256(input_bytes: Sequence[bytes]) -> bytearray:
    # https://github.com/ethereum/eth-hash/blob/master/eth_hash/backends/pycryptodome.py#L37
    # ETH_DIGEST_BITS = 256
    # digest_bytes = 256 // 8 = 32
    # https://github.com/Legrandin/pycryptodome/blob/master/lib/Crypto/Hash/keccak.py#L73
    # capacity_in_bytes = digest_bytes *2 = 64
    # rate_bits = 1600 - capacity_in_bits = 1600 - 512 = 1088

    # https://github.com/Legrandin/pycryptodome/blob/5dace638b70ac35bb5d9b565f3e75f7869c9d851/lib/Crypto/Hash/keccak.py#L74
    delimitedSuffix = 0x01

    return keccak_full(1088, 512, input_bytes, delimitedSuffix, 256 // 8)


def test_keccak():
    _input = "abcde".encode("utf8")
    from eth_hash.auto import keccak

    assert keccak_256(_input) == keccak(_input)
