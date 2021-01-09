import pytest
from misc_crypto.ecc import BLS12381Backend, BN254Backend


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_Fq(backend):
    Fq = backend.Fq()
    assert Fq(2) * Fq(2) == Fq(4)
    assert Fq(2) / Fq(7) + Fq(9) / Fq(7) == Fq(11) / Fq(7)
    assert Fq(2) * Fq(7) + Fq(9) * Fq(7) == Fq(11) * Fq(7)
    assert Fq(9) ** backend.field_modulus == Fq(9)
    assert Fq(-1).n > 0


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_G1(backend):
    G1 = backend.G1()

    assert G1.double().add(G1).add(G1).eq(G1.double().double())
    assert not G1.double().eq(G1)
    assert G1.multiply(9).add(G1.multiply(5)).eq(G1.multiply(12).add(G1.multiply(2)))
    assert G1.multiply(backend.curve_order).is_inf()


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_G2(backend):
    G2 = backend.G2()
    assert G2.double().add(G2).add(G2).eq(G2.double().double())
    assert not G2.double().eq(G2)
    assert G2.multiply(9).add(G2.multiply(5)).eq(G2.multiply(12).add(G2.multiply(2)))
    assert G2.multiply(backend.curve_order).is_inf()
    assert not G2.multiply(2 * backend.field_modulus - backend.curve_order).is_inf()
