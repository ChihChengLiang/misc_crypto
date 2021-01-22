from misc_crypto.utils.assembly import OPCODES
from eth_utils import decode_hex, encode_hex
import re

bytecode = "0x60806040526000805534801561001457600080fd5b5060ab806100236000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c8063209652551460375780635524107714604f575b600080fd5b603d606b565b60408051918252519081900360200190f35b606960048036036020811015606357600080fd5b50356071565b005b60005490565b60005556fea265627a7a72315820eb0499b2b3b5d05773fb5abc6caf5e3100bfb59d07f243593f2d723c8a14b46364736f6c63430005110032"


def get_generator(bytecode: str):
    codes = decode_hex(bytecode)
    for code in codes:
        yield code


REVERSE_OPCODE = {0x56: "JUMP", 0x57: "JUMPI", 0x5B: "JUMPDEST"}
for k, v in OPCODES.items():
    REVERSE_OPCODE[v] = k


def parse_meta(bytecode: str):
    """
    https://ethereum.stackexchange.com/questions/23525/what-is-the-cryptic-part-at-the-end-of-a-solidity-contract-bytecode
    """
    codes = decode_hex(bytecode)
    regex = b"\xa2\x65bzzr(.{1})\x58\x20(.{32})\x64solc\x43(.{3})\x00\x32"

    bzz_version, bzz_hash, solc_version = re.findall(regex, codes)[0]
    solc = ".".join([str(i) for i in solc_version])
    print(f"bzzr{bzz_version}", encode_hex(bzz_hash))
    print("solidity", solc)


def decompile(bytecode: str):
    parse_meta(bytecode)
    gen = get_generator(bytecode.split("a265")[0])
    while True:
        code = next(gen)
        opcode = None
        data = None
        if 0x60 <= code <= 0x7F:
            length = code - 0x5F
            opcode = f"PUSH{length}"
            data = [hex(next(gen)) for _ in range(length)]
        elif 0x80 <= code <= 0x8F:
            length = code - 0x7F
            opcode = f"DUP{length}"
        elif 0x90 <= code <= 0x9F:
            length = code - 0x8F
            opcode = f"SWAP{length}"
        else:
            opcode = REVERSE_OPCODE[code]
        print(opcode.upper(), end="")
        if data is not None:
            print("\t", data, len(data))
        else:
            print()


decompile(bytecode)
