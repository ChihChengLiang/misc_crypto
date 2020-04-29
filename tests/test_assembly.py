import pytest

from misc_crypto.utils.assembly import Contract


def test_simple_assembly_code():
    contract = Contract().push(0)
    tx_data = contract.create_tx_data()

    assert tx_data.startswith("0x")
