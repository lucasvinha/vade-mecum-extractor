import pytest

from vademecum.modelo import chave_de_texto, chave_ordenacao


def test_h12_sufixo_vazio_ordena_antes_de_letra():
    assert chave_ordenacao(121, ()) < chave_ordenacao(121, ("A",))


@pytest.mark.parametrize(
    "cadeia",
    [
        ["121", "121-A", "121-B", "122"],
        ["359-M", "359-M-A", "359-M-B", "359-N"],  # H12
    ],
)
def test_ordem_da_chave_de_texto(cadeia):
    chaves = [chave_de_texto(s) for s in cadeia]
    assert chaves == sorted(chaves)
    assert len(set(chaves)) == len(chaves)


@pytest.mark.parametrize(
    ("texto", "chave"),
    [
        # Formas reais do `arts` dos tópicos do edital.
        ("1º", (1, ())),  # H11
        ("12", (12, ())),
        ("396-A", (396, ("A",))),
        ("1.169", (1169, ())),  # P13
        ("1.091-A", (1091, ("A",))),  # P13
        ("359-M-A", (359, ("M", "A"))),  # H12
        # H11: grau e letra "o" como ordinal, inclusive antes do sufixo (`§ 2o-A`).
        ("2°", (2, ())),
        ("4o", (4, ())),
        ("2o-A", (2, ("A",))),
    ],
)
def test_h11_h12_p13_chave_de_texto(texto, chave):
    assert chave_de_texto(texto) == chave


@pytest.mark.parametrize("texto", ["Art. 121", "121-a", "", "1.09", "121-", "121 "])
def test_chave_de_texto_rejeita_forma_fora_do_fragmento(texto):
    with pytest.raises(ValueError):
        chave_de_texto(texto)
