from dataclasses import replace

import pytest

from vademecum.modelo import Base, EntradaRelatorio, Metadados, No, Norma, Nota, Relatorio
from vademecum.perfil import carregar_perfil
from vademecum.validador import validar

_NORMA = Norma(
    id="cp",
    titulo="DECRETO-LEI No 2.848, DE 7 DE DEZEMBRO DE 1940",
    ementa="Código Penal.",
    tipo_fonte="html",
    fonte="cp.mht",
    capturado_em="2026-10-26T02:03:12Z",
    sha256="0" * 64,
    perfil="cp",
)
_NOTA_OUTRA = Nota(tipo="outra", bruto="(Lei nº 7.209, de 11.7.1984)")


def _artigo(numero, *filhos, sufixo=(), texto="texto vigente.", notas=()):
    id_ = "-".join(("art" + str(numero), *sufixo))
    return No(
        id=id_,
        tipo="artigo",
        texto=texto,
        origem=f"html:p#{numero}",
        numero=numero,
        sufixo=sufixo,
        notas=notas,
        filhos=filhos,
    )


def _no(id_, tipo, texto="texto vigente.", *filhos, notas=()):
    return No(id=id_, tipo=tipo, texto=texto, origem=f"html:{id_}", notas=notas, filhos=filhos)


def _avisos(artigos, perfil="cp", entradas=()):
    relatorio = Relatorio()
    for entrada in entradas:
        relatorio.registrar(entrada)
    validar(
        Base(norma=_NORMA, metadados=Metadados(), artigos=artigos),
        carregar_perfil(perfil),
        relatorio,
    )
    return [(e.texto, e.origem) for e in relatorio.entradas if e.tipo == "aviso"]


def _descarte_de_artigo(numero):
    return EntradaRelatorio(
        tipo="descarte", origem=f"html:p#{numero}", texto="", id=f"art{numero}", motivo="revogado"
    )


def test_base_valida_nao_gera_aviso():
    artigos = (
        _artigo(1),
        _artigo(
            2, _no("art2.p1", "paragrafo"), _no("art2.p2", "paragrafo"), _no("art2.pu", "paragrafo")
        ),
        _artigo(2, sufixo=("A",)),
        _artigo(3, _no("art3.pena1", "pena", "")),
    )
    assert _avisos(artigos) == []


def test_validar_nao_muda_a_base_e_so_registra_aviso():
    relatorio = Relatorio()
    base = Base(norma=_NORMA, metadados=Metadados(), artigos=(_artigo(2), _artigo(1)))
    validar(base, carregar_perfil("cp"), relatorio)
    assert [a.id for a in base.artigos] == ["art2", "art1"]
    assert {e.tipo for e in relatorio.entradas} == {"aviso"}


def test_v1_artigo_fora_de_ordem():
    assert _avisos((_artigo(1), _artigo(3), _artigo(2))) == [
        ("V1: art2 fora de ordem, depois de art3", "html:p#2")
    ]


def test_v1_sufixo_ordena_depois_do_numero_sem_sufixo():
    # H12: `359-M` < `359-M-A` < `359-N` (A6).
    artigos = (
        _artigo(359, sufixo=("M",)),
        _artigo(359, sufixo=("M", "A")),
        _artigo(359, sufixo=("N",)),
    )
    assert [texto for texto, _ in _avisos(artigos) if not texto.startswith("V2")] == []


def test_v2_lacuna_na_numeracao_base():
    assert _avisos((_artigo(1), _artigo(4))) == [
        ("V2: lacuna na numeração-base: art. 2", "html:p#4"),
        ("V2: lacuna na numeração-base: art. 3", "html:p#4"),
    ]


def test_v2_descarte_de_artigo_preenche_a_lacuna():
    # H19, ADR-003: o artigo revogado conta pelo descarte de artigo; o de parágrafo, não.
    paragrafo = replace(_descarte_de_artigo(3), id="art3.p1")
    assert _avisos((_artigo(1), _artigo(4)), entradas=(_descarte_de_artigo(2), paragrafo)) == [
        ("V2: lacuna na numeração-base: art. 3", "html:p#4")
    ]


def test_v2_desligada_pelo_perfil():
    perfil = replace(carregar_perfil("cp"), lacunas=False)
    relatorio = Relatorio()
    base = Base(norma=_NORMA, metadados=Metadados(), artigos=(_artigo(1), _artigo(4)))
    validar(base, perfil, relatorio)
    assert relatorio.entradas == ()


def test_v3_id_duplicado_na_arvore():
    artigos = (_artigo(1, _no("art1.p1", "paragrafo"), _no("art1.p1", "paragrafo")),)
    assert _avisos(artigos) == [("V3: id duplicado: art1.p1 (2 vezes)", "html:art1.p1")]


def test_v3_mesmo_segmento_em_pais_diferentes_nao_e_duplicado():
    artigos = (_artigo(1, _no("art1.p1", "paragrafo")), _artigo(2, _no("art2.p1", "paragrafo")))
    assert _avisos(artigos) == []


@pytest.mark.parametrize(
    "ids, tipo",
    [
        (("art1.p2", "art1.p1"), "paragrafo"),
        (("art1.p2-A", "art1.p2"), "paragrafo"),
        (("art1.i3", "art1.i2"), "inciso"),
        (("art1.b", "art1.a"), "alinea"),
    ],
)
def test_v4_irmao_menor_depois_de_maior(ids, tipo):
    artigos = (_artigo(1, *(_no(id_, tipo) for id_ in ids)),)
    assert _avisos(artigos) == [
        (f"V4: {ids[1]} fora de ordem, depois de {ids[0]}", f"html:{ids[1]}")
    ]


def test_v4_tipos_diferentes_e_paragrafo_unico_nao_se_comparam():
    # Inciso do caput antes do § 1º, e penas intercaladas (H14), seguem a ordem do texto.
    artigos = (
        _artigo(
            1,
            _no("art1.i2", "inciso"),
            _no("art1.pena1", "pena"),
            _no("art1.p1", "paragrafo", "texto.", _no("art1.p1.i1", "inciso")),
            _no("art1.pu", "paragrafo"),
        ),
    )
    assert _avisos(artigos) == []


def test_v5_texto_vazio_em_dispositivo_vigente():
    # ADR-001: o nó vazio com filho vigente fica na base, e a V5 o acusa.
    artigos = (_artigo(1, _no("art1.p2", "paragrafo", "", _no("art1.p2.i1", "inciso"))),)
    assert _avisos(artigos) == [("V5: texto vazio em dispositivo vigente: art1.p2", "html:art1.p2")]


def test_v5_pena_vazia_nao_gera_aviso():
    assert _avisos((_artigo(1, _no("art1.pena1", "pena", "")),)) == []


def test_v6_nota_outra_sem_registro_no_relatorio():
    artigos = (_artigo(1, notas=(_NOTA_OUTRA,)),)
    assert _avisos(artigos) == [
        ("V6: nota outra sem registro no relatório: (Lei nº 7.209, de 11.7.1984)", "html:p#1")
    ]


def test_v6_nota_outra_registrada_nao_gera_aviso():
    registro = EntradaRelatorio(tipo="nota_outra", origem="html:p#1", texto=_NOTA_OUTRA.bruto)
    assert _avisos((_artigo(1, notas=(_NOTA_OUTRA,)),), entradas=(registro,)) == []
