from misc_crypto.utils.assembly import Contract
from .poseidon import get_constants, get_matrix, Fr
from eth_utils import decode_hex
from py_ecc.bn128 import curve_order
from typing import Union


def to_32bytes(a: Union[int, Fr]):
    return int(a).to_bytes(32, "big")


def save_matrix(contract, matrix, t):
    for i, row in enumerate(matrix):
        for j, element in enumerate(row):
            (
                contract.push(to_32bytes(element))
                .push((1 + i * t + j) * 32)
                .mstore()
            )


def ark(contract, constants, r, t):
    contract.push(to_32bytes(constants[r]))  # K, st, q
    for i in range(t):
        (
            contract.dup(1 + t)  # q, K, st, q
            .dup(1)  # K, q, K, st, q
            .dup(3 + i)  # st[i], K, q, K, st, q
            .addmod()  # newSt[i], K, st, q
            .swap(2 + i)  # xx, K, st, q
            .pop()
        )
    contract.pop()


def sigma(contract, p, t):
    (
        contract.dup(t)  # sq, q  # q, st, q
        .dup(1 + p)  # st[p] , q , st, q
        .dup(1)  # q, st[p] , q , st, q
        .dup(0)  # q, q, st[p] , q , st, q
        .dup(2)  # st[p] , q, q, st[p] , q , st, q
        .dup(0)  # st[p] , st[p] , q, q, st[p] , q , st, q
        .mulmod()  # st2[p], q, st[p] , q , st, q
        .dup(0)  # st2[p], st2[p], q, st[p] , q , st, q
        .mulmod()  # st4[p], st[p] , q , st, q
        .mulmod()  # st5[p], st, q
        .swap(1 + p)
        .pop()  # newst, q
    )


def mix(contract, t):
    contract.label("mix")
    for i in range(t):
        for j in range(t):
            if j == 0:
                (
                    contract.dup(i + t)  # q, newSt, oldSt, q
                    .push((1 + i * t + j) * 32)
                    .mload()  # M, q, newSt, oldSt, q
                    .dup(2 + i + j)  # oldSt[j], M, q, newSt, oldSt, q
                    .mulmod()  # acc, newSt, oldSt, q
                )
            else:
                (
                    contract.dup(1 + i + t)  # q, acc, newSt, oldSt, q
                    .push((1 + i * t + j) * 32)
                    .mload()  # M, q, acc, newSt, oldSt, q
                    .dup(3 + i + j)  # oldSt[j], M, q, acc, newSt, oldSt, q
                    .mulmod()  # aux, acc, newSt, oldSt, q
                    .dup(2 + i + t)  # q, aux, acc, newSt, oldSt, q
                    .swap(2)  # acc, aux, q, newSt, oldSt, q
                    .addmod()  # acc, newSt, oldSt, q
                )
    for i in range(t):
        contract.swap((t - i) + (t - i - 1)).pop()
    contract.push(0).mload().jmp()


def create_code(t, roundsF, roundsP, seed):
    matrix = get_matrix(t, seed)
    constants = get_constants(t, seed, roundsF + roundsP)

    contract = Contract()

    # Check selector
    (
        contract.push(b"\x01" + b"\x00" * 28)
        .push(0)
        .calldataload()
        .div()
        .push("0xc4420fb4")  # poseidon(uint256[])
        .eq()
        .jmpi("start")
        .invalid()
    )

    contract.label("start")

    save_matrix(contract, matrix, t)

    contract.push(to_32bytes(curve_order))  # The number is also the field modulus of Fr

    # Load 6 values from the call data.
    # The function has a single array param param
    # [Selector (4)] [Pointer (32)][Length (32)] [data1 (32)] ....
    # We ignore the pointer and the length and just load 6 values to the state
    # (Stack positions 0-5) If the array is shorter, we just set zeros.
    for i in range(t):
        contract.push(0x44 + (0x20 * (5 - i))).calldataload()

    for i in range(roundsF + roundsP):
        ark(contract, constants, i, t)
        if i < roundsF / 2 or i >= roundsP + roundsF / 2:
            for j in range(t):
                sigma(contract, j, t)
        else:
            sigma(contract, 0, t)

        str_label = f"after_mix_{i}"
        (
            contract._push_label(str_label)
            .push(0)
            .mstore()
            .jmp("mix")
            .label(str_label)
        )
    (
        contract.push(0)
        .mstore()  # Save it to position 0
        .push(0x20)
        .push(0x00)
        .return_()
    )

    mix(contract, t)

    return contract.create_tx_data()


ABI = [
    {
        "constant": True,
        "inputs": [{"name": "input", "type": "uint256[]"}],
        "name": "poseidon",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "pure",
        "type": "function",
    }
]
