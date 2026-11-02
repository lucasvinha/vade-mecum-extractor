"""Curadoria do vade mecum: marcas, teto e penas dos quadros contra o recorte (ver ADR-006)."""

import dataclasses
from pathlib import Path

import pytest

from vademecum.curadoria import CelulaPena, Marca, Pena, interpretar_pena, validar_curadoria
from vademecum.modelo import ErroFonte, Relatorio, de_json
from vademecum.recorte import interpretar, recortar

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
BASE = de_json((FIXTURES / "snapshots" / "cp_enxertos.json").read_text(encoding="utf-8"))
RECORTE = recortar(BASE, interpretar("121"), (), Relatorio())


def _curadoria(dispositivos=None, quadros=()):
    return {
        "schema": "curadoria-vm/1",
        "edital": "oj26",
        "materia": "penal",
        "gerado_em": "2026-11-02",
        "dispositivos": dispositivos or {},
        "quadros": list(quadros),
    }


def _validar(dispositivos=None, quadros=(), recortes=(RECORTE,)):
    return validar_curadoria(_curadoria(dispositivos, quadros), recortes)


def _erros(dispositivos=None, quadros=()):
    return [str(erro) for erro in _validar(dispositivos, quadros).erros]


def _quadro(*celulas):
    return {
        "depois_de": "cp:art121",
        "titulo": "Homicídio",
        "colunas": [f"c{n}" for n in range(len(celulas))],
        "linhas": [list(celulas)],
    }


# --- Penas: texto real do recorte do CP × forma resumida do quadro ---------------------------


@pytest.mark.parametrize(
    ("recorte", "quadro"),
    [
        ("reclusão, de dois a doze anos, e multa.", "reclusão, 2 a 12 anos, e multa"),  # 312
        ("reclusão, de 2 (dois) a 12 (doze) anos, e multa.", "reclusão, 2 a 12 anos, e multa"),
        ("reclusão, de 20 (vinte) a 40 (quarenta anos).", "reclusão, 20 a 40 anos"),  # 121 § 2º-D
        ("detenção, de três meses a um ano.", "detenção, 3 meses a 1 ano"),  # 129
        ("detenção, de quinze dias a um mês, ou multa.", "detenção, 15 dias a 1 mês, ou multa"),
        ("detenção, de três meses a um ano, além da multa.", "detenção, 3 meses a 1 ano, e multa"),
        ("Detenção, de três meses a um ano, e multa.", "detenção, três meses a um ano, e multa"),
    ],
)
def test_adr006_pena_resumida_bate_com_a_do_recorte(recorte, quadro):
    assert interpretar_pena(recorte) == interpretar_pena(quadro) is not None


def test_adr006_pena_interpretada_por_partes():
    # 320: as pontas têm unidades diferentes, e a multa é alternativa.
    pena = interpretar_pena("detenção, de quinze dias a um mês, ou multa.")
    assert pena == Pena("detenção", (15, "dia"), (1, "mes"), "alternativa")
    # 321, parágrafo único: "além da multa" é cumulativa.
    pena = interpretar_pena("detenção, de três meses a um ano, além da multa.")
    assert pena == Pena("detenção", (3, "mes"), (1, "ano"), "cumulativa")
    # 314: a oração depois da faixa não é conferida.
    pena = interpretar_pena(
        "reclusão, de um a quatro anos, se o fato não constitui crime mais grave."
    )
    assert pena == Pena("reclusão", (1, "ano"), (4, "ano"), "ausente")


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("reclusão, de dois a doze anos, e multa.", "detenção, 2 a 12 anos, e multa"),
        ("reclusão, de dois a doze anos, e multa.", "reclusão, 2 a 8 anos, e multa"),
        ("reclusão, de dois a doze anos, e multa.", "reclusão, 2 a 12 anos"),
        ("detenção, de quinze dias a um mês, ou multa.", "detenção, 15 dias a 1 mês, e multa"),
        ("detenção, de três meses a um ano.", "detenção, 3 a 12 meses"),
    ],
)
def test_adr006_pena_divergente(a, b):
    assert interpretar_pena(a) != interpretar_pena(b)


@pytest.mark.parametrize(
    "texto",
    [
        # 299: duas faixas, por documento público e particular.
        "reclusão, de um a cinco anos, e multa, se o documento é público, e reclusão de um a três "
        "anos, e multa, de quinhentos mil réis a cinco contos de réis, se o documento é "
        "particular.",
        "a cominada à falsificação ou à alteração.",  # 304: remissão
        "reclusão, 2 a 12 anos + multa",
    ],
)
def test_adr006_pena_nao_interpretavel(texto):
    assert interpretar_pena(texto) is None


# --- Marcas ----------------------------------------------------------------------------------


def test_adr006_marca_vira_posicao_no_texto():
    validacao = _validar({"cp:art121": {"marcas": [{"trecho": "Matar", "cat": "verbo"}]}})
    assert validacao.erros == ()
    assert validacao.curadoria.dispositivos["cp:art121"].marcas == (Marca(0, 5, "verbo"),)


def test_adr006_marca_em_nfc_aponta_o_texto_original():
    # art. 339 do CP: a fonte traz "à" decomposto (NFD); a marca procura em NFC.
    artigo = dataclasses.replace(RECORTE.artigos[0], texto="Dar causa à instauração")
    recorte = dataclasses.replace(RECORTE, artigos=(artigo,))
    dispositivos = {"cp:art121": {"marcas": [{"trecho": "à instauração", "cat": "verbo"}]}}
    validacao = _validar(dispositivos, recortes=(recorte,))
    (marca,) = validacao.curadoria.dispositivos["cp:art121"].marcas
    assert artigo.texto[marca.inicio : marca.fim] == "à instauração"


@pytest.mark.parametrize(
    ("marcas", "erro"),
    [
        ([{"trecho": "Matar alguém", "cat": "verbo"}], "trecho não encontrado: 'Matar alguém'"),
        ([{"trecho": "a", "cat": "verbo"}], "trecho ambíguo: 'a'"),
        ([{"trecho": "Matar", "cat": "pena"}], "cat fora da lista: 'pena'"),
        (
            [{"trecho": "Matar", "cat": "verbo"}, {"trecho": "ar alguem", "cat": "sujeito"}],
            "trecho sobreposto a outra marca: 'ar alguem'",
        ),
    ],
)
def test_adr006_marca_com_erro(marcas, erro):
    # O texto legal é literal: "alguem", sem acento, como no Planalto.
    assert _erros({"cp:art121": {"marcas": marcas}}) == [f"cp:art121: {erro}"]


def test_adr006_id_inexistente_e_erro():
    assert _erros({"cp:art999": {"atencao": ["x"]}}) == ["cp:art999: id inexistente no recorte"]


def test_adr006_teto_de_marcas_so_avisa():
    # O artigo 121 tem muito texto nos filhos: marcar o caput inteiro não passa do teto.
    dispositivos = {"cp:art121": {"marcas": [{"trecho": "Matar alguem:", "cat": "verbo"}]}}
    assert _validar(dispositivos).avisos == ()
    artigo = dataclasses.replace(RECORTE.artigos[0], filhos=())
    recorte = dataclasses.replace(RECORTE, artigos=(artigo,))
    validacao = _validar(dispositivos, recortes=(recorte,))
    assert validacao.erros == ()
    assert [str(a) for a in validacao.avisos] == [
        "cp:art121: marcas cobrem 100% do artigo (teto ~15%)"
    ]


# --- Quadros ---------------------------------------------------------------------------------


def test_adr006_quadro_com_pena_conferida():
    celula = {"pena": "cp:art121.p2-D.pena1", "texto": "reclusão, 20 a 40 anos"}
    validacao = _validar(quadros=[_quadro("Art. 121, § 2º-D", celula)])
    assert validacao.erros == ()
    (quadro,) = validacao.curadoria.quadros
    assert quadro.linhas == (
        ("Art. 121, § 2º-D", CelulaPena("cp:art121.p2-D.pena1", "reclusão, 20 a 40 anos")),
    )


def test_adr006_pena_literal_sai_com_o_texto_do_recorte():
    validacao = _validar(quadros=[_quadro({"pena": "cp:art121.pena1"})])
    assert validacao.erros == ()
    (celula,) = validacao.curadoria.quadros[0].linhas[0]
    assert celula == CelulaPena("cp:art121.pena1", "reclusão, de seis a vinte anos.")


def test_adr006_pena_do_quadro_com_erro():
    erros = _erros(
        quadros=[
            _quadro(
                {"pena": "cp:art121.pena1", "texto": "reclusão, 6 a 12 anos"},
                {"pena": "cp:art121.pena1", "texto": "reclusão + multa"},
                {"pena": "cp:art121", "texto": "reclusão, 6 a 20 anos"},
            )
        ]
    )
    assert erros == [
        "quadro 1, linha 1: cp:art121.pena1: pena divergente: no quadro 'reclusão, 6 a 12 anos', "
        "no recorte 'reclusão, de seis a vinte anos.'",
        "quadro 1, linha 1: cp:art121.pena1: pena do quadro não interpretável: 'reclusão + multa'",
        "quadro 1, linha 1: pena inexistente no recorte: cp:art121",
    ]


def test_adr006_pena_do_recorte_nao_interpretavel_pede_a_literal():
    # 299: duas faixas; com `texto` é erro, sem ele a célula sai literal.
    pena = dataclasses.replace(
        RECORTE.artigos[0].filhos[0],
        texto="reclusão, de um a cinco anos, e multa, se o documento é público, e reclusão de um "
        "a três anos, e multa, se o documento é particular.",
    )
    artigo = dataclasses.replace(RECORTE.artigos[0], filhos=(pena,))
    recorte = dataclasses.replace(RECORTE, artigos=(artigo,))
    assert pena.tipo == "pena"
    com_texto = {"pena": f"cp:{pena.id}", "texto": "reclusão, 1 a 5 anos, e multa"}
    erros = validar_curadoria(_curadoria(quadros=[_quadro(com_texto)]), (recorte,)).erros
    assert [e.motivo.split(",")[0] for e in erros] == ["pena do recorte não interpretável"]
    sem_texto = validar_curadoria(
        _curadoria(quadros=[_quadro({"pena": f"cp:{pena.id}"})]), (recorte,)
    )
    assert sem_texto.erros == ()


def test_adr006_quadro_depois_de_inexistente():
    quadro = dict(_quadro("x"), depois_de="cp:art122")
    assert _erros(quadros=[quadro]) == ["quadro 1: depois_de inexistente no recorte: cp:art122"]


# --- Forma -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "dados",
    [
        {"schema": "curadoria-vm/2"},
        {k: v for k, v in _curadoria().items() if k != "gerado_em"},
        dict(_curadoria(), dispositivos=[]),
        dict(_curadoria(), quadros=[dict(_quadro("a", "b"), linhas=[["a"]])]),
    ],
)
def test_adr006_forma_invalida_e_erro_de_entrada(dados):
    with pytest.raises(ErroFonte):
        validar_curadoria(dados, (RECORTE,))
