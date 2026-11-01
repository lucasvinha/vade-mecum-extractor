import pytest

pytestmark = pytest.mark.aceite


def test_a4_revogado_o_livramento_e_texto_vigente(cp_parser, no):
    # H15: `Revogado` no início do texto não é revogação.
    base, _ = cp_parser
    art88 = no(base, "art88")
    assert art88["texto"].startswith("Revogado o livramento, não poderá ser novamente concedido")
    assert art88["rubrica"] == "Efeitos da revogação"
    assert [nota["tipo"] for nota in art88["notas"]] == ["redacao"]
