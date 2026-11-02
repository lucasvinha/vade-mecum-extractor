import pytest

from vademecum.modelo import ErroFonte
from vademecum.recorte import Item, interpretar


def _faixas(expressao):
    return [(item.inicio, item.fim) for item in interpretar(expressao)]


@pytest.mark.parametrize(
    "expressao",
    [
        # `arts` de claude/topicos-oj2026.json.
        "1º a 12",
        "8º; 9º; 18; 19",
        "1.169 a 1.173",
        "396; 396-A",
        "792; 798; 798-A",
        "1.431; 1.432; 1.442; 1.444 a 1.447; 1.451; 1.461; 1.467 a 1.472",
        # MD do conteúdo programático do edital.
        "1º–4º",
        "12; 13",
        "994–1.091; 1.091-A",
        "439; 440; 440-A",
        "196, inciso XX",
        "282, § 1º",
        # Exemplo de negocio/recorte-e-cli.
        "1-12; 100-120; 121; 129; 150; 154; 293-305; 307; 308; 311-A; 312-317",
    ],
)
def test_rf18_linhas_reais_do_edital_sao_aceitas(expressao):
    assert interpretar(expressao)


def test_separador_de_item_ponto_e_virgula_ou_virgula():
    assert _faixas("8º; 9º") == _faixas("8º, 9º") == [((8, ()), (8, ())), ((9, ()), (9, ()))]


@pytest.mark.parametrize("expressao", ["1º a 12", "1º–12", "1º-12", "1 - 12"])
def test_faixa_com_hifen_travessao_ou_a(expressao):
    assert _faixas(expressao) == [((1, ()), (12, ()))]


@pytest.mark.parametrize(
    ("expressao", "faixa"),
    [
        ("1º–4º", ((1, ()), (4, ()))),  # H11: ordinal nas duas pontas
        ("1.169 a 1.173", ((1169, ()), (1173, ()))),  # P13: milhar nas duas pontas
        ("994–1.091", ((994, ()), (1091, ()))),
    ],
)
def test_h11_p13_ordinal_e_milhar_opcionais_nas_pontas(expressao, faixa):
    assert _faixas(expressao) == [faixa]


@pytest.mark.parametrize(
    ("expressao", "faixa"),
    [
        ("359-M-A", ((359, ("M", "A")), (359, ("M", "A")))),  # H12: letra depois de `-` é sufixo
        ("121-A–130", ((121, ("A",)), (130, ()))),
        ("994-1.091", ((994, ()), (1091, ()))),  # dígito depois de `-` fecha a faixa
    ],
)
def test_h12_hifen_com_letra_e_sufixo_e_com_digito_e_faixa(expressao, faixa):
    assert _faixas(expressao) == [faixa]


def test_p1_avulso_e_so_o_artigo_citado():
    [item] = interpretar("121")
    assert item == Item(texto="121", inicio=(121, ()), fim=(121, ()))


def test_adr004_faixa_guarda_as_chaves_das_pontas():
    [item] = interpretar(" 121-130 ")
    assert item == Item(texto="121-130", inicio=(121, ()), fim=(130, ()))


@pytest.mark.parametrize(
    ("expressao", "qualificadores"),
    [
        ("196, inciso XX", ("inciso XX",)),
        ("282, § 1º", ("§ 1º",)),
        ("196, incisos XX; XXI", ("incisos XX", "XXI")),
    ],
)
def test_p2_qualificador_fica_preso_ao_item_anterior(expressao, qualificadores):
    [item] = interpretar(expressao)
    assert item.qualificadores == qualificadores
    assert item.inicio == item.fim


def test_p2_qualificador_nao_passa_para_o_item_seguinte():
    itens = interpretar("196, inciso XX; 197")
    assert [item.qualificadores for item in itens] == [("inciso XX",), ()]


def test_itens_saem_na_ordem_escrita():
    assert [item.texto for item in interpretar("120-125; 121")] == ["120-125", "121"]


@pytest.mark.parametrize(
    ("expressao", "mensagem"),
    [
        ("inciso XX", "qualificador sem artigo antes.*'inciso XX'"),
        ("abc", "qualificador sem artigo antes.*'abc'"),  # não começa com dígito
        ("121-", "ilegível.*'121-'"),
        ("121-a", "ilegível.*'121-a'"),
        ("1-2-3", "ilegível.*'1-2-3'"),
        ("121; 12x", "ilegível.*'12x'"),
        ("130-121", "faixa invertida.*'130-121'"),
        ("121-A–121", "faixa invertida.*'121-A–121'"),
        ("", "item vazio"),
        ("121;; 122", "item vazio"),
    ],
)
def test_expressao_invalida_levanta_erro_fonte_com_o_item(expressao, mensagem):
    with pytest.raises(ErroFonte, match=mensagem):
        interpretar(expressao)
