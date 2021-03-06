import pytest
from hashlib import blake2b
from misc_crypto.poseidon import (
    get_pseudo_random,
    get_matrix,
    poseidon_t6,
    Poseidon,
)
from misc_crypto.poseidon.utils import recommend_parameter
from misc_crypto.poseidon.parameter_finder import find_parameter


def test_blake2b_version():
    h = blake2b(b"poseidon_constants", digest_size=32).hexdigest()
    assert h == "e57ba154fb2c47811dc1a2369b27e25a44915b4e4ece4eb8ec74850cb78e01b1"


def test_get_pseudo_random():
    assert get_pseudo_random(b"poseidon", 5) == (
        15824101442726336678493729790213225602337266391839199937743631806357667769936,
        21242663800926259018279473475394539681984199997998092992785924410742632368937,
        7537673755943127760422551293899591957569458436859277585653724494712104093827,
        13103956771683026785204972701532832557470888040257734043695564144998080518407,
        14473492389881884561010535037929347039894105704213210537867280693408016123791,
    )


def test_get_matrix():
    assert get_matrix(2, b"poseidon") == (
        (
            5905559862616915807900579325651902433433685645159267419610962108431726462693,
            12711080208452642132636348910936535131635469619255658927004323269777977499766,
        ),
        (
            1630059164638566989648383609786744055995088365519873639181021774367459228529,
            18634098492055214324873285470566015538548967469826511946578953323931218028182,
        ),
    )


def test_poseidon():
    expected = (
        12242166908188651009877250812424843524687801523336557272219921456462821518061
    )
    assert poseidon_t6([1, 2]) == expected


@pytest.mark.parametrize("elements_length", range(2, 27))
def test_recommended_parameter(elements_length):
    assert recommend_parameter(elements_length) == find_parameter(elements_length + 1)


def test_from_elements_length():
    poseidon_l5 = Poseidon.from_elements_length(5)
    assert Poseidon(6, 8, 50).hash([1, 2]) == poseidon_l5.hash([1, 2])
