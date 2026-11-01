import pytest

pytestmark = pytest.mark.aceite

# O enxerto vai até o art. 191; o CP inteiro, em `dados/`, traz o Título III até o 196.
NO_ENXERTO = [f"art{numero}" for numero in range(187, 192)]
NO_CP_INTEIRO = [f"art{numero}" for numero in range(187, 197)]


def _confere(base: dict, relatorio: dict, ids: list[str]) -> None:
    # ADR-001, RF14: revogados pela Lei 9.279/1996, saem da base.
    assert {artigo["id"] for artigo in base["artigos"]}.isdisjoint(ids)
    # RF16: um descarte de artigo por número, com o rótulo e a nota de revogação.
    descartes = {e["id"]: e for e in relatorio["entradas"] if e["tipo"] == "descarte"}
    for id_ in ids:
        assert descartes[id_]["motivo"] == "revogado"
        # Rótulo literal: `Art 187.` e `Art 188.` vêm sem o ponto do prefixo na fonte (P9).
        assert descartes[id_]["rotulo"].endswith(f" {id_.removeprefix('art')}")
        assert "revogacao" in [nota["tipo"] for nota in descartes[id_]["notas"]]


def test_a5_arts_187_a_191_ausentes_e_registrados_no_enxerto(cp_enxertos):
    _confere(*cp_enxertos, NO_ENXERTO)


def test_a5_arts_187_a_196_ausentes_e_registrados_no_cp_inteiro(cp_inteiro):
    _confere(*cp_inteiro, NO_CP_INTEIRO)
