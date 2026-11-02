import pytest

from vademecum.modelo import Base, Metadados, No, Norma, Relatorio, chave_de_texto, id_artigo
from vademecum.recorte import interpretar, recortar

pytestmark = pytest.mark.aceite

ROTULOS = ["120", "121", "121-A", "121-B", *map(str, range(122, 131)), "130-A", "131"]


def _artigo(rotulo):
    numero, sufixo = chave_de_texto(rotulo)
    return No(
        id=id_artigo(numero, sufixo),
        tipo="artigo",
        texto=f"texto do art. {rotulo}",
        origem="",
        rotulo=f"Art. {rotulo}",
        numero=numero,
        sufixo=sufixo,
    )


def test_a13_faixa_121_130_traz_as_letras_de_dentro_e_nao_130_a():
    # ADR-004: a faixa vai de chave(121) a chave(130), e 130-A vem depois de 130.
    norma = Norma("cp", "Código Penal", None, "html", "cp.htm", "2026-10-26T02:03:12Z", "0", "cp")
    base = Base(norma=norma, metadados=Metadados(), artigos=tuple(map(_artigo, ROTULOS)))
    relatorio = Relatorio()
    recorte = recortar(base, interpretar("121-130"), (), relatorio)
    rotulos = [artigo.rotulo.removeprefix("Art. ") for artigo in recorte.artigos]
    assert rotulos == ["121", "121-A", "121-B", *map(str, range(122, 131))]
    assert relatorio.entradas == ()
