import pytest
from misc_crypto.ecc import BLS12381Backend, BN254Backend, pairing_check


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_Fq(backend):
    Fq = backend.Fq
    assert Fq(2) * Fq(2) == Fq(4)
    assert Fq(2) / Fq(7) + Fq(9) / Fq(7) == Fq(11) / Fq(7)
    assert Fq(2) * Fq(7) + Fq(9) * Fq(7) == Fq(11) * Fq(7)
    assert Fq(9) ** backend.field_modulus == Fq(9)
    assert Fq(-1).n > 0


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_G1(backend):
    G1 = backend.get_G1()

    assert G1.double().add(G1).add(G1).eq(G1.double().double())
    assert not G1.double().eq(G1)
    assert G1.multiply(9).add(G1.multiply(5)).eq(G1.multiply(12).add(G1.multiply(2)))
    assert G1.multiply(backend.curve_order).is_inf()


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_G2(backend):
    G2 = backend.get_G2()
    assert G2.double().add(G2).add(G2).eq(G2.double().double())
    assert not G2.double().eq(G2)
    assert G2.multiply(9).add(G2.multiply(5)).eq(G2.multiply(12).add(G2.multiply(2)))
    assert G2.multiply(backend.curve_order).is_inf()
    assert not G2.multiply(2 * backend.field_modulus - backend.curve_order).is_inf()


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_pairing_negative_G1(backend):
    G1 = backend.get_G1()
    G2 = backend.get_G2()
    pairing = backend.pairing
    p1 = pairing(G1, G2)
    pn1 = pairing(G1.neg(), G2)

    assert p1 * pn1 == backend.FQ12One()


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_pairing_negative_G2(backend):
    G1 = backend.get_G1()
    G2 = backend.get_G2()
    pairing = backend.pairing

    p1 = pairing(G1, G2)
    pn1 = pairing(G1.neg(), G2)
    np1 = pairing(G1, G2.neg())

    assert p1 * np1 == backend.FQ12One()
    assert pn1 == np1


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_pairing_output_order(backend):
    p1 = backend.pairing(backend.get_G1(), backend.get_G2())
    assert p1 ** backend.curve_order == backend.FQ12One()


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_pairing_bilinearity_on_G1(backend):
    G1 = backend.get_G1()
    G2 = backend.get_G2()
    pairing = backend.pairing

    p1 = pairing(G1, G2)
    p2 = pairing(G1.multiply(2), G2)

    assert p1 * p1 == p2


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_pairing_is_non_degenerate(backend):
    G1 = backend.get_G1()
    G2 = backend.get_G2()
    pairing = backend.pairing

    p1 = pairing(G1, G2)
    p2 = pairing(G1.multiply(2), G2)
    np1 = pairing(G1, G2.neg())

    assert p1 != p2 and p1 != np1 and p2 != np1


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_pairing_bilinearity_on_G2(backend):
    G1 = backend.get_G1()
    G2 = backend.get_G2()
    pairing = backend.pairing

    p1 = pairing(G1, G2)
    p2 = pairing(G1, G2.multiply(2))

    assert p1 * p1 == p2


@pytest.mark.parametrize("backend", (BLS12381Backend, BN254Backend))
def test_pairing_composit_check(backend):
    G1 = backend.get_G1()
    G2 = backend.get_G2()
    pairing = backend.pairing

    p3 = pairing(G1.multiply(37), G2.multiply(27))
    po3 = pairing(G1.multiply(999), G2)
    assert p3 == po3

    assert pairing_check(
        backend, G1.multiply(37), G2.multiply(27), G1.multiply(999), G2.neg()
    )
