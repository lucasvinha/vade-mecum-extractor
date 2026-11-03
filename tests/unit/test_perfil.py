import re
from dataclasses import replace

import pytest

from vademecum import perfil as modulo
from vademecum.modelo import ErroFonte
from vademecum.perfil import Perfil, carregar_perfil


def test_cp_herda_o_padrao_e_liga_a_rubrica_sem_negrito():
    cp = carregar_perfil("cp")
    assert isinstance(cp, Perfil)
    assert cp.id == "cp"
    assert cp.rubrica_sem_negrito is True  # H6 (c)
    assert cp.prefixos_artigo == ("Art.", "Art", "Artigo")  # P9
    assert cp.niveis == ("PARTE", "LIVRO", "TÍTULO", "CAPÍTULO", "Seção", "Subseção")  # H5
    assert (cp.rubrica, cp.pena, cp.lacunas) == (True, True, True)
    assert cp.rodape_inicio  # H17
    tipos = [tipo for tipo, _ in cp.notas]
    assert tipos == ["redacao", "inclusao", "revogacao", "veto", "vigencia", "remissao"]
    assert dict(cp.notas)["redacao"] == ("Redação dada", "NR")  # P16


@pytest.mark.parametrize("nome", ["cpp", "lei9099"])
def test_perfil_minimo_so_troca_o_id_do_padrao(nome):
    # M7: sem perfil próprio, a base sai com id `padrao` e o recorte não casa com a `norma`.
    assert carregar_perfil(nome) == replace(carregar_perfil("padrao"), id=nome)


def test_padrao_nao_liga_a_rubrica_sem_negrito():
    padrao = carregar_perfil("padrao")
    assert (padrao.id, padrao.rubrica_sem_negrito) == ("padrao", False)


def test_rodape_do_padrao_casa_o_rodape_real_do_cp():
    [inicio] = carregar_perfil("cp").rodape_inicio
    # H17: CP, a linha logo depois do art. 361.
    assert re.match(inicio, "Rio de Janeiro, 7 de dezembro de 1940; 119º da Independência e 52º")
    assert re.match(inicio, "Brasília, 16 de março de 2015; 194º da Independência e 127º")
    assert not re.match(inicio, "Art. 361 - Este Código entrará em vigor no dia 1º de janeiro")


def test_perfil_e_imutavel():
    with pytest.raises(AttributeError):
        carregar_perfil("cp").id = "outro"  # type: ignore[misc]


def test_perfil_inexistente_levanta_erro_fonte():
    with pytest.raises(ErroFonte, match="perfil inexistente: 'xyz'"):
        carregar_perfil("xyz")


@pytest.mark.parametrize(
    ("dados", "chave"),
    [({"idd": "cp"}, "idd"), ({"rubrica": {"sem_negritos": True}}, "rubrica.sem_negritos")],
)
def test_chave_desconhecida_levanta_erro_fonte(dados, chave):
    with pytest.raises(ErroFonte, match=f"chave desconhecida no perfil 'x': {chave}"):
        modulo._validar(dados, "x")


def test_mescla_sobrescreve_so_a_chave_que_o_especifico_traz():
    base = {"id": "padrao", "rubrica": {"sem_negrito": False}, "notas": {"veto": ["VETADO"]}}
    mesclado = modulo._mesclar(base, {"id": "cp", "notas": {"veto": ["Vetado"]}})
    assert mesclado == {
        "id": "cp",
        "rubrica": {"sem_negrito": False},
        "notas": {"veto": ["Vetado"]},
    }
