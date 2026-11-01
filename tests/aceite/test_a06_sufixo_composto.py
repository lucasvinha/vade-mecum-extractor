import pytest

pytestmark = pytest.mark.aceite


def test_a6_359_m_a_e_m_b_entre_359_m_e_359_n(cp_parser):
    # H12: sufixo de dois níveis; a ordem é a do texto, que já segue a chave de ordenação.
    base, _ = cp_parser
    ids = [artigo["id"] for artigo in base["artigos"]]
    posicao = {id_: ids.index(id_) for id_ in ("art359-M", "art359-M-A", "art359-M-B", "art359-N")}
    assert posicao["art359-M"] < posicao["art359-M-A"] < posicao["art359-M-B"] < posicao["art359-N"]
    m_a = base["artigos"][posicao["art359-M-A"]]
    assert (m_a["rotulo"], m_a["numero"], m_a["sufixo"]) == ("Art. 359-M-A", 359, ["M", "A"])
