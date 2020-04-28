from eth_utils import encode_hex, decode_hex, is_hex
from typing import List, Dict, Sequence, Union, Optional

OPCODES = {
    "stop": 0x00,
    "add": 0x01,
    "mul": 0x02,
    "sub": 0x03,
    "div": 0x04,
    "sdi": 0x05,
    "mod": 0x06,
    "smod": 0x07,
    "addmod": 0x08,
    "mulmod": 0x09,
    "exp": 0x0A,
    "signextend": 0x0B,
    "lt": 0x10,
    "gt": 0x11,
    "slt": 0x12,
    "sgt": 0x13,
    "eq": 0x14,
    "iszero": 0x15,
    "and": 0x16,
    "or": 0x17,
    "shor": 0x18,
    "not": 0x19,
    "byte": 0x1A,
    "kecca": 0x20,
    "sha": 0x20,  # alias of kecca
    "address": 0x30,
    "balance": 0x31,
    "origin": 0x32,
    "caller": 0x33,
    "callvalue": 0x34,
    "calldataload": 0x35,
    "calldatasize": 0x36,
    "calldatacopy": 0x37,
    "codesize": 0x38,
    "codecopy": 0x39,
    "gasprice": 0x3A,
    "extcodesize": 0x3B,
    "extcodecopy": 0x3C,
    "returndatasize": 0x3D,
    "returndatacopy": 0x3E,
    "blockhash": 0x40,
    "coinbase": 0x41,
    "timestamp": 0x42,
    "number": 0x43,
    "difficulty": 0x44,
    "gaslimit": 0x45,
    "pop": 0x50,
    "mload": 0x51,
    "mstore": 0x52,
    "mstore8": 0x53,
    "sload": 0x54,
    "sstore": 0x55,
    "pc": 0x58,
    "msize": 0x59,
    "gas": 0x5A,
    "log0": 0xA0,
    "log1": 0xA1,
    "log2": 0xA2,
    "log3": 0xA3,
    "log4": 0xA4,
    "create": 0xF0,
    "call": 0xF1,
    "callcode": 0xF2,
    "return_": 0xF3,  # avoid python reserved word
    "delegatecall": 0xF4,
    "staticcall": 0xFA,
    "revert": 0xFD,
    "invalid": 0xFE,
    "selfdestruct": 0xFF,
}


def to_big_endian(x: int) -> bytes:
    if x == 0:
        return b"\x00"
    else:
        return x.to_bytes((x.bit_length() + 7) // 8, "big")


class Contract:
    code: List[int]
    labels: Dict[str, int]
    pending_labels: Dict[str, List[int]]

    def __init__(self):
        self.code = []
        self.labels = {}
        self.pending_labels = {}

    def create_tx_data(self):
        if len(self.pending_labels.keys()) > 0:
            raise ValueError(f"Lables not defined: {self.pending_labels.keys()}")

        set_loader_length = 0
        loaded_length = 11  # initialize with minium possible len(loader.code)

        while set_loader_length != loaded_length:
            set_loader_length = loaded_length
            loader = (
                Contract()
                .codesize()
                .push(set_loader_length)
                .push(b"\x00")
                .codecopy()
                .push(len(self.code))
                .push(b"\x00")
                .return_()
            )
            loaded_length = len(loader.code)

        return encode_hex(bytes(loader.code + self.code))

    def __getattr__(self, name):
        """
        Call opcodes with no arguments
        """

        def method():
            try:
                opcode = OPCODES[name]
            except KeyError:
                raise ValueError(f"Invalid Opcode: {name}")
            self.code.append(opcode)
            return self

        return method

    def _push_label(self, label: str) -> "Contract":
        if label in self.labels:
            self.push(self.labels[label])
        else:
            if label not in self.pending_labels:
                self.pending_labels[label] = []
            self.pending_labels[label] += [len(self.code)]
            self.push(b"\x00\x00\x00")
        return self

    def _fill_label(self, label: str) -> None:
        if label not in self.pending_labels:
            return

        dst = self.labels[label]
        dst3 = [dst >> 16, (dst >> 8) & 0xFF, dst & 0xFF]
        for position in self.pending_labels[label]:
            for i, dsti in enumerate(dst3):
                self.code[position + i + 1] = dsti
        del self.pending_labels[label]

    def jmp(self, label: str = None) -> "Contract":
        if label is not None:
            self._push_label(label)
        self.code.append(0x56)
        return self

    def jmpi(self, label: str) -> "Contract":
        if label is None:
            raise ValueError(f"Invalid label: {label}")
        self._push_label(label)
        self.code.append(0x57)
        return self

    def label(self, name: str) -> "Contract":
        if name in self.labels:
            raise ValueError(f"Label already defined: {name}")
        self.labels[name] = len(self.code)
        self.code.append(0x5B)
        self._fill_label(name)
        return self

    def push(self, input_data: Union[bytes, str, int]) -> "Contract":
        """
        Opcode push1(0x60) to push32(0x7f), the length of data determines which opcode to use
        """
        data: bytes
        if isinstance(input_data, bytes):
            data = input_data
        elif isinstance(input_data, int):
            data = to_big_endian(input_data)
        elif is_hex(input_data):
            data = decode_hex(input_data)
        else:
            raise TypeError(f"Unsupported input_data type: {type(input_data)}")

        len_data = len(data)
        if len_data == 0 or len_data > 32:
            raise ValueError(f"Invalid data length: {len_data}")

        # If the data has length 5, the opcode for push5 is 0x5F + 5
        self.code.append(0x5F + len_data)
        self.code.extend([d for d in data])
        return self

    def dup(self, n: int) -> "Contract":
        """
        Opcode dup1 to dup16, duplicate the nth stack item
        """
        if n < 0 or n >= 16:
            raise ValueError(f"Invalid n: {n}")
        self.code.append(0x80 + n)
        return self

    def swap(self, n: int) -> "Contract":
        """
        Opcode swap1 to swap16
        """
        if n < 0 or n >= 16:
            raise ValueError(f"Invalid n: {n}")
        self.code.append(0x8F + n)
        return self
