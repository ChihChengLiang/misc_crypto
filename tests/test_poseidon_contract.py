import pytest
from misc_crypto.poseidon.contract import create_code, ABI
from misc_crypto.poseidon import Poseidon
from web3 import Web3, EthereumTesterProvider
from eth_utils import decode_hex


def get_deployed(abi, bytecode):
    w3 = Web3(EthereumTesterProvider())
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = contract.constructor().transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    instance = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
    return instance


def test_deployment():
    poseidon = Poseidon(6, 8, 57)

    contract_code = create_code(6, 8, 57, poseidon.matrix, poseidon.constants)
    poseidon_contract = get_deployed(abi=ABI, bytecode=decode_hex(contract_code))
    hash_output = poseidon_contract.functions.poseidon([1, 2]).call()

    assert poseidon.hash([1, 2]) == hash_output
