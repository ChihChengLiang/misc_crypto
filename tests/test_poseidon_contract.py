import pytest
from misc_crypto.poseidon.contract import create_code




def test_poseidon_contract():
    contract = create_code(6, 8, 57, b"poseidon")
