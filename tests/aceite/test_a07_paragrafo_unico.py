import pytest

pytestmark = pytest.mark.aceite


def test_a7_art2_paragrafo_unico(cp_parser, no):
    base, _ = cp_parser
    [pu] = no(base, "art2")["filhos"]
    assert (pu["id"], pu["tipo"], pu["rotulo"]) == ("art2.pu", "paragrafo", "Parágrafo único")
    assert pu["texto"].startswith("A lei posterior, que de qualquer modo favorecer o agente")
