import pytest

pytestmark = pytest.mark.aceite


def test_a3_paragrafos_2b_2c_2d_presentes(cp_enxertos, no):
    base, _ = cp_enxertos
    ids = [filho["id"] for filho in no(base, "art121")["filhos"]]
    for id_ in ("art121.p2-B", "art121.p2-C", "art121.p2-D"):
        assert id_ in ids
    assert ids.index("art121.p2-B") < ids.index("art121.p2-C") < ids.index("art121.p2-D")


def test_a3_paragrafo_2d_com_pena_propria(cp_enxertos, no):
    base, _ = cp_enxertos
    [pena] = no(base, "art121.p2-D")["filhos"]
    assert (pena["id"], pena["tipo"]) == ("art121.p2-D.pena1", "pena")
    assert pena["texto"] == "reclusão, de 20 (vinte) a 40 (quarenta anos)."


def test_a3_paragrafos_2a_e_7_ausentes(cp_enxertos, no):
    # ADR-001: revogados, saem da base e ficam nos descartes (RF16).
    base, relatorio = cp_enxertos
    ids = [filho["id"] for filho in no(base, "art121")["filhos"]]
    descartados = {
        e.get("id"): e["motivo"] for e in relatorio["entradas"] if e["tipo"] == "descarte"
    }
    for id_ in ("art121.p2-A", "art121.p7"):
        assert id_ not in ids
        assert descartados[id_] == "revogado"
