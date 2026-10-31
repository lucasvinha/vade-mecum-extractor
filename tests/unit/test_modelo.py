import dataclasses
import typing

import pytest

from vademecum.modelo import (
    Base,
    ErroFonte,
    LinhaFonte,
    Local,
    Metadados,
    No,
    Norma,
    Nota,
    Recorte,
    chave_de_texto,
    chave_ordenacao,
)


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


_NOTA = Nota(tipo="redacao", bruto="(Redação dada pela Lei nº 15.134, de 2025)")
_ALINEA = No(id="art121.p2.i7.a", tipo="alinea", texto="autoridade ou agente…", origem="html:p#9")
_NORMA = Norma(
    id="cp",
    titulo="DECRETO-LEI No 2.848, DE 7 DE DEZEMBRO DE 1940",
    ementa="Código Penal.",
    tipo_fonte="html",
    fonte="https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm",
    capturado_em="2026-10-26T02:03:12Z",
    sha256="0" * 64,
    perfil="cp",
)
_INSTANCIAS = [
    LinhaFonte(
        texto="Matar alguem:",
        negrito=False,
        rotulo_negrito=False,
        centralizado=False,
        cor=None,
        origem="html:p#1",
    ),
    _NOTA,
    Local(parte="PARTE ESPECIAL"),
    _ALINEA,
    _NORMA,
    Metadados(),
    Recorte(expressao="121-130; 311-A", origem="base_cp.json"),
    Base(norma=_NORMA, metadados=Metadados(), artigos=(_ALINEA,)),
]


@pytest.mark.parametrize("obj", _INSTANCIAS, ids=lambda o: type(o).__name__)
def test_dataclasses_sao_frozen_e_slots(obj):
    assert not hasattr(obj, "__dict__")
    campo = dataclasses.fields(obj)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(obj, campo, None)


@pytest.mark.parametrize(
    ("classe", "campo"), [(No, "filhos"), (No, "notas"), (No, "sufixo"), (Base, "artigos")]
)
def test_colecoes_da_arvore_sao_tuple(classe, campo):
    assert typing.get_origin(typing.get_type_hints(classe)[campo]) is tuple
    padrao = {f.name: f.default for f in dataclasses.fields(classe)}[campo]
    assert padrao == ()


def test_no_aninha_filhos_e_notas():
    inciso = No(
        id="art121.p2.i7",
        tipo="inciso",
        texto="contra:",
        origem="html:p#8",
        rotulo="VII",
        notas=(_NOTA,),
        filhos=(_ALINEA,),
    )
    assert inciso.filhos[0] is _ALINEA
    assert inciso.notas[0].data is None


def test_campos_da_linha_fonte_sao_os_do_contrato():
    # Ver negocio/pipeline-e-perfis: o contrato central do pipeline.
    nomes = [f.name for f in dataclasses.fields(LinhaFonte)]
    assert nomes == ["texto", "negrito", "rotulo_negrito", "centralizado", "cor", "origem"]


def test_campos_do_local_sao_os_do_esquema():
    nomes = {f.name for f in dataclasses.fields(Local)}
    assert nomes == {"parte", "livro", "titulo", "capitulo", "secao", "subsecao", "rotulo_livre"}


def test_campos_da_nota_sao_os_do_esquema():
    nomes = {f.name for f in dataclasses.fields(Nota)}
    assert nomes == {"tipo", "norma", "ano", "data", "bruto"}


def test_rf06_erro_fonte_e_exception():
    with pytest.raises(ErroFonte, match="PDF sem texto"):
        raise ErroFonte("PDF sem texto")
    assert issubclass(ErroFonte, Exception)
