import pytest

pytestmark = pytest.mark.aceite

# Parte estrutural da A2. O VI revogado e a rubrica `Feminicídio` dele ainda estão na árvore: a
# ausência dos dois vem com o filtro de vigência (ADR-001, H16).


def test_a2_paragrafo_2_com_incisos_e_duas_penas_posicionais(cp_enxertos, no):
    base, _ = cp_enxertos
    p2 = no(base, "art121.p2")
    assert [(f["tipo"], f.get("rotulo")) for f in p2["filhos"]] == [
        ("inciso", "I"),
        ("inciso", "II"),
        ("inciso", "III"),
        ("inciso", "IV"),
        ("inciso", "V"),
        ("pena", None),
        ("inciso", "VI"),
        ("inciso", "VII"),
        ("inciso", "VIII"),
        ("inciso", "IX"),
        ("inciso", "X"),
        ("pena", None),
    ]  # H14
    assert [f["id"] for f in p2["filhos"] if f["tipo"] == "pena"] == [
        "art121.p2.pena1",
        "art121.p2.pena2",
    ]


def test_a2_inciso_vii_com_alineas_a_e_b(cp_enxertos, no):
    base, _ = cp_enxertos
    vii = no(base, "art121.p2.i7")
    assert vii["texto"] == "contra:"
    assert [(f["id"], f["tipo"]) for f in vii["filhos"]] == [
        ("art121.p2.i7.a", "alinea"),
        ("art121.p2.i7.b", "alinea"),
    ]
