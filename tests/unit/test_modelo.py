import dataclasses
import typing

import pytest

from vademecum.modelo import (
    TIPOS_ENTRADA,
    Base,
    EntradaRelatorio,
    ErroFonte,
    LinhaFonte,
    Local,
    Metadados,
    No,
    Norma,
    Nota,
    Recorte,
    Relatorio,
    chave_de_texto,
    chave_ordenacao,
    id_alinea,
    id_artigo,
    id_inciso,
    id_paragrafo,
    id_pena,
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


@pytest.mark.parametrize(
    ("rotulo", "esperado"),
    [
        ("121", "art121"),
        ("121-A", "art121-A"),
        ("359-M-A", "art359-M-A"),  # H12
        ("1.091-A", "art1091-A"),  # P13: o id leva o número sem o ponto do milhar
    ],
)
def test_p13_id_do_artigo_deriva_do_rotulo(rotulo, esperado):
    assert id_artigo(*chave_de_texto(rotulo)) == esperado


def test_id_do_artigo_sem_sufixo_por_padrao():
    assert id_artigo(121) == "art121"


@pytest.mark.parametrize(
    ("rotulo", "esperado"),
    [("2º", "art121.p2"), ("2º-B", "art121.p2-B"), ("4o", "art121.p4")],  # A3, A8
)
def test_id_do_paragrafo_numerado(rotulo, esperado):
    assert id_paragrafo("art121", *chave_de_texto(rotulo)) == esperado


def test_a7_id_do_paragrafo_unico():
    assert id_paragrafo("art2", None) == "art2.pu"


@pytest.mark.parametrize(
    ("romano", "numero"),
    [("I", 1), ("IV", 4), ("VII", 7), ("IX", 9), ("X", 10), ("XL", 40), ("LXXVIII", 78)],
)
def test_id_do_inciso_converte_o_romano(romano, numero):
    assert id_inciso("art121.p2", romano) == f"art121.p2.i{numero}"


@pytest.mark.parametrize("romano", ["", "IIII", "VX", "vii", "VII-A", "7"])
def test_id_do_inciso_rejeita_romano_invalido(romano):
    with pytest.raises(ValueError, match="inciso romano"):
        id_inciso("art121.p2", romano)


def test_id_encadeia_pai_e_segmento():
    # O exemplo do art. 121 em negocio/modelo-de-dados.
    paragrafo = id_paragrafo(id_artigo(121), 2)
    assert id_alinea(id_inciso(paragrafo, "VII"), "a") == "art121.p2.i7.a"


def test_a2_id_das_penas_conta_no_mesmo_pai():
    assert [id_pena("art121", n) for n in (1, 2)] == ["art121.pena1", "art121.pena2"]


def test_id_da_pena_comeca_em_1():
    with pytest.raises(ValueError, match="pena"):
        id_pena("art121", 0)


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
    EntradaRelatorio(tipo="aviso", origem="pdf:p3:col2:l14", texto="Parágrafo único."),
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


def test_rnf04_tipos_de_entrada_sao_os_do_contrato():
    esperados = {"descarte", "aviso", "nao_classificada", "nota_outra", "faixa_revogada"}
    assert esperados == TIPOS_ENTRADA


@pytest.mark.parametrize("tipo", sorted(TIPOS_ENTRADA))
def test_rnf04_entrada_aceita_os_cinco_tipos(tipo):
    entrada = EntradaRelatorio(tipo=tipo, origem="html:p#1", texto="VI - (Revogado)")
    assert entrada.tipo == tipo


@pytest.mark.parametrize("tipo", ["outra", "Aviso", "revogado", ""])
def test_rnf04_entrada_rejeita_tipo_fora_dos_cinco(tipo):
    with pytest.raises(ValueError, match="tipo de entrada"):
        EntradaRelatorio(tipo=tipo, origem="html:p#1", texto="x")


def test_rnf04_relatorio_guarda_na_ordem_do_registro():
    relatorio = Relatorio()
    assert relatorio.entradas == ()
    # P11 e P15: os dois casos reais que motivam faixa_revogada e aviso.
    faixa = EntradaRelatorio(
        tipo="faixa_revogada", origem="pdf:p40:col1:l3", texto="Art. 1.054 a Art. 1091. Revogados."
    )
    aviso = EntradaRelatorio(tipo="aviso", origem="pdf:p7:col2:l9", texto="Parágrafo único.")
    descarte = EntradaRelatorio(tipo="descarte", origem="html:p#12", texto="Feminicídio")
    for entrada in (faixa, aviso, descarte):
        relatorio.registrar(entrada)
    assert relatorio.entradas == (faixa, aviso, descarte)


def test_relatorio_so_muda_por_registrar():
    relatorio = Relatorio()
    assert not hasattr(relatorio, "__dict__")
    assert isinstance(relatorio.entradas, tuple)
    with pytest.raises(AttributeError):
        relatorio.entradas = ()  # type: ignore[misc]
