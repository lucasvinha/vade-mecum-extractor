import re

import pytest

from vademecum.modelo import chave_de_texto

pytestmark = pytest.mark.aceite


def test_a1_numeracao_base_de_1_a_361_sem_lacuna(cp_inteiro):
    # H19, ADR-003: o artigo revogado sai da base (ADR-001), mas conta pelo descarte de artigo.
    base, relatorio = cp_inteiro
    numeros = {artigo["numero"] for artigo in base["artigos"]}
    descartados = {
        chave_de_texto(e["id"].removeprefix("art"))[0]
        for e in relatorio["entradas"]
        if e["tipo"] == "descarte" and e["id"] is not None and "." not in e["id"]
    }
    assert sorted(numeros | descartados) == list(range(1, 362))
    assert {185, 187, 196, 350} <= descartados - numeros
    assert base["artigos"][-1]["id"] == "art361"


def test_a1_rodape_fora_da_arvore(cp_inteiro, no):
    base, _ = cp_inteiro
    assert no(base, "art361")["texto"] == (
        "Este Código entrará em vigor no dia 1º de janeiro de 1942."
    )
    assert base["metadados"]["rodape"].startswith("Rio de Janeiro, 7 de dezembro de 1940;")
    assert base["norma"]["titulo"] == "DECRETO-LEI No 2.848, DE 7 DE DEZEMBRO DE 1940"
    assert base["norma"]["ementa"] == "Código Penal."


def test_a1_nenhuma_linha_sem_classificacao(cp_inteiro):
    # RNF04: toda linha está na árvore, nos metadados ou numa entrada tipada do relatório.
    _, relatorio = cp_inteiro
    assert [e for e in relatorio["entradas"] if e["tipo"] == "nao_classificada"] == []


def test_a1_validador_so_acusa_o_art_272(cp_inteiro):
    # V1–V6 no CP inteiro: o único aviso é a V4 do art. 272, cujo § 1º-A vem antes do § 1º na
    # própria fonte (H20). A regra não se afrouxa: o aviso é o esperado.
    _, relatorio = cp_inteiro
    avisos = [
        (e["texto"], e["origem"])
        for e in relatorio["entradas"]
        if e["tipo"] == "aviso" and re.match(r"V\d: ", e["texto"])
    ]
    assert avisos == [("V4: art272.p1 fora de ordem, depois de art272.p1-A", "html:p#1747")]
