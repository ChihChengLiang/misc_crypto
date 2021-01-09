from misc_crypto.utils.assembly import Contract
from typing import Union, Sequence
from .fields import Fr

# Note to reviewers:
# This module contains evm assemply operations.
# The state of evm stacks are commented to help you reason with the code.
# https://ethervm.io/ is also very helpful.
# There's a gotcha though.
# When we write `state[p]` in comment, we are using the python index, which starts from zero. The first item is state[0]
# But for the evm stack, the dup1 is duplicating the top of the stack.


# The number is also the curve order of bn128
q = Fr.field_modulus


def to_32bytes(x: Union[int, Fr]):
    return int(x).to_bytes(32, "big")


def save_matrix(contract: Contract, t: int, matrix):
    for i, row in enumerate(matrix):
        for j, element in enumerate(row):
            (
                contract.push(to_32bytes(element))
                .push((1 + i * t + j) * 32)  # Store in different memory position
                .mstore()
            )


def ark(contract: Contract, t: int, c: Fr):
    # state, q
    contract.push(to_32bytes(c))
    # c, state, q
    for i in range(t):
        (
            contract.dup(2 + t)
            # q, c, state, q
            .dup(2)
            # c, q, c, state, q
            .dup(4 + i)
            # st[i], c, q, c, state, q
            .addmod()
            # newSt[i], c, state, q
            .swap(2 + i)
            # _, c, state, q
            .pop()
            # c, state, q
        )
    contract.pop()
    # state, q


def sigma(contract: Contract, t: int, p: int):
    (
        # state, q
        contract.dup(t + 1)
        # q, state, q
        .dup(2 + p)
        # state[p] , q , state, q
        .dup(2)
        # q, state[p] , q , state, q
        .dup(1)
        # q, q, state[p] , q , state, q
        .dup(3)
        # state[p] , q, q, state[p] , q , state, q
        .dup(1)
        # state[p], state[p], q, q, state[p] , q , state, q
        .mulmod()
        # state[p]**2, q, state[p] , q , state, q
        .dup(1)
        # state[p]**2, state[p]**2, q, state[p] , q , state, q
        .mulmod()  # st4[p], st[p] , q , st, q
        # state[p]**4, state[p] , q , state, q
        .mulmod()
        # state[p]**5, state, q
        .swap(1 + p)
        # _, new_state, q
        .pop()
        # new_state, q
    )


def mix(contract, t):
    contract.label("mix")
    for i in range(t):
        for j in range(t):
            if j == 0:
                (
                    # new_state[i-1...0], old_state[0...t-1], q
                    contract.dup(i + t + 1)
                    # q, new_state, old_state, q
                    .push((1 + i * t + j) * 32).mload()
                    # Mij, q, new_state, old_state, q
                    .dup(3 + i + j)
                    # old_state[j], Mij, q, new_state, old_state, q
                    .mulmod()  # accumulation, new_state, old_state, q
                )
            else:
                (
                    # accumulation, new_state, old_state, q
                    contract.dup(2 + i + t)
                    # q, accumulation, new_state, old_state, q
                    .push((1 + i * t + j) * 32).mload()
                    # Mij, q, accumulation, new_state, old_state, q
                    .dup(4 + i + j)
                    # old_state[j], Mij, q, accumulation, new_state, old_state, q
                    .mulmod()
                    # Mij*sj, accumulation, new_state, old_state, q
                    .dup(3 + i + t)
                    # q, Mij*sj, accumulation, new_state, old_state, q
                    .swap(2)
                    # accumulation, Mij*sj, q, new_state, old_state, q
                    .addmod()
                    # new_accumulation, new_state, old_state, q
                )
            # The last new_accumulation is the new_state[i + 1]

    # Reverse the new_state and pop out the old_state
    # new_state[t-1...0], old_state[0...t-1], q
    for i in range(t):
        (
            # {     t-i items    }, {     t-i items    }, {      i items   }
            # new_state[t-i-1...0], old_state[0...t-i-1], new_state[t-i...t-1], q
            contract.swap((t - i) + (t - i - 1))
            # old_state[t-i], new_state[t-i-2...0], old_state[0...t-1-i], new_state[t-i-1], new_state[t-i...t-1], q
            .pop()
        )
    # Go to position 0
    contract.push(0).mload().jmp()


def check_selector(contract: Contract, signature4bytes: str) -> None:
    """
    Check if the evm message selects the correct function's 4 bytes signature
    """
    (
        contract.push(b"\x01" + b"\x00" * 28)
        .push(0)
        .calldataload()
        .div()
        .push(signature4bytes)
        .eq()
        .jmpi("start")
        .invalid()
    )


def create_code(
    t: int,
    roundsF: int,
    roundsP: int,
    matrix: Sequence[Sequence[Fr]],
    constants: Sequence[Fr],
) -> str:
    contract = Contract()
    check_selector(contract, "0xc4420fb4")  # poseidon(uint256[])

    contract.label("start")

    save_matrix(contract, t, matrix)

    # field modulus is always at the bottom of the stack
    contract.push(to_32bytes(q))

    # Load t values from the call data.
    # The function has a single array param param
    # [Selector (4)] [Pointer (32)][Length (32)] [data1 (32)] ....
    # We ignore the pointer and the length and just load t values to the state
    # (Stack positions 1...t) If the array is shorter, we just set zeros.
    for i in range(t):
        contract.push(0x44 + (0x20 * (t - 1 - i))).calldataload()

    for i in range(roundsF + roundsP):
        ark(contract, t, constants[i])
        if i < roundsF / 2 or i >= roundsP + roundsF / 2:
            for j in range(t):
                sigma(contract, t, j)
        else:
            sigma(contract, t, 0)

        str_label = f"after_mix_{i}"
        (contract._push_label(str_label).push(0).mstore().jmp("mix").label(str_label))
    (
        contract
        # Save output to memory position 0
        .push(0)
        .mstore()
        # Return 64 bytes from memory
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
