from eth_utils import encode_hex, decode_hex, is_hex
from typing import List, Dict, Union

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
    "shl": 0x1B,
    "shr": 0x1C,
    "sar": 0x1D,
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


# For a label that's not yet defined, we leave a 3 bytes placeholder
# We fill the placeholder with the actual instruction position when the label is defined.
LABEL_POSITION_PLACEHOLDER = b"\x00\x00\x00"


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
        """
        If the label is already defined, we fill in the label's instruction position
        When the label is undefined, we leave a placeholder and record the position that needs
        to fill in the label's instruction position later.
        """
        if label in self.labels:
            self.push(self.labels[label])
        else:
            if label not in self.pending_labels:
                self.pending_labels[label] = []
            self.pending_labels[label] += [len(self.code)]
            self.push(LABEL_POSITION_PLACEHOLDER)
        return self

    def _fill_label(self, label: str) -> None:
        if label not in self.pending_labels:
            return

        # Replace the 3 bytes LABEL_POSITION_PLACEHOLDER with the label's actual position
        destination_3bytes = self.labels[label].to_bytes(3, "big")
        for position in self.pending_labels[label]:
            for i, byte in enumerate(destination_3bytes):
                self.code[position + i + 1] = byte
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
        self.code.append(0x5B)  # jumpdest
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
        Opcode dup1(0x80) to dup16(0x8F), duplicate the nth stack item
        """
        if n < 1 or n > 16:
            raise ValueError(f"Invalid n: {n}")
        self.code.append(0x7F + n)
        return self

    def swap(self, n: int) -> "Contract":
        """
        Opcode swap1(0x90) to swap16(0x9F), swap top and (n+1)th stack items
        """
        if n < 1 or n > 16:
            raise ValueError(f"Invalid n: {n}")
        self.code.append(0x8F + n)
        return self
