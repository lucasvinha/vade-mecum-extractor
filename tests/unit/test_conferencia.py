"""`conferir`: o texto legal do HTML do vade mecum contra os recortes (ver ADR-005)."""

from pathlib import Path

import pytest

from vademecum.conferencia import Divergencia, conferir
from vademecum.modelo import Relatorio, de_json
from vademecum.recorte import interpretar, recortar

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
HTML = (FIXTURES / "vade-mecum" / "cp_art121.html").read_text(encoding="utf-8")
BASE = de_json((FIXTURES / "snapshots" / "cp_enxertos.json").read_text(encoding="utf-8"))
RECORTE = recortar(BASE, interpretar("121"), (), Relatorio())


def _conferir(html, recortes=(RECORTE,)):
    return [str(divergencia) for divergencia in conferir(recortes, html)]


def _trocar(antes, depois):
    assert HTML.count(antes) == 1, antes
    return HTML.replace(antes, depois)


def test_adr005_html_correto_sem_divergencia():
    # A fixture tem anotações sem `data-id` (aviso, quadro, `<mark>`), que não são conferidas.
    assert _conferir(HTML) == []


def test_adr005_no_ausente():
    inicio = HTML.index('<div class="inciso" data-id="art121.p2.i2">')
    fim = HTML.index("</div>", inicio) + len("</div>")
    assert _conferir(HTML[:inicio] + HTML[fim:]) == ["cp:art121.p2.i2: nó ausente"]


def test_adr005_campo_divergente():
    # Texto legal é literal: "futil" sem acento, como no Planalto, não se corrige.
    html = _trocar("por motivo futil;", "por motivo fútil;")
    assert _conferir(html) == [
        "cp:art121.p2.i2: campo texto divergente: esperado 'por motivo futil;', "
        "no HTML 'por motivo fútil;'"
    ]


def test_adr005_data_id_desconhecido():
    html = _trocar("</article>", '<p data-id="art121.p2.i6">revogado</p></article>')
    assert _conferir(html) == ["cp:art121.p2.i6: data-id desconhecido"]


def test_adr005_data_id_repetido():
    html = _trocar("</article>", '<div data-id="art121.pena1"></div></article>')
    assert _conferir(html) == ["cp:art121.pena1: data-id repetido"]


def test_adr005_espacos_colapsados_e_sem_os_das_pontas():
    html = _trocar(
        '<span data-campo="texto">por motivo futil;</span>',
        '<span data-campo="texto">\n   por&nbsp;motivo\n  futil; </span>',
    )
    assert _conferir(html) == []


_INCISO_II = (
    '<strong data-campo="rotulo">II</strong> <span data-campo="texto">por motivo futil;</span>'
)


@pytest.mark.parametrize(
    ("depois", "motivos"),
    [
        (
            '<strong>II</strong> <span data-campo="texto">por motivo futil;</span>',
            ["rotulo ausente"],
        ),
        (_INCISO_II + '<b data-campo="rubrica">x</b>', ["rubrica a mais"]),
        (_INCISO_II + '<i data-campo="texto">;</i>', ["texto repetido"]),
        (_INCISO_II + '<i data-campo="nota">x</i>', ["nota desconhecido"]),
    ],
)
def test_adr005_campo_ausente_a_mais_repetido_ou_desconhecido(depois, motivos):
    divergencias = _conferir(_trocar(_INCISO_II, depois))
    assert divergencias == [f"cp:art121.p2.i2: campo {motivo}" for motivo in motivos]


def test_adr005_campo_do_filho_nao_conta_para_o_pai():
    # O texto do inciso I fica dentro do campo do § 2º, mas o `data-id` mais próximo dele é o do
    # inciso: o § 2º continua só com "Se o homicídio é cometido:".
    html = _trocar(
        '<span data-campo="texto">Se o homicídio é cometido:</span></p>',
        '<span data-campo="texto">Se o homicídio é cometido:<i data-id="x">ignorado</i></span></p>',
    )
    assert _conferir(html) == ["cp:x: data-id desconhecido"]


def test_adr005_data_id_fora_de_norma_e_de_outra_norma():
    html = _trocar(
        "</body>", '<p data-id="art1"></p><div data-norma="cpp"><p data-id="art1"></p></div></body>'
    )
    assert _conferir(html) == ["-:art1: data-id desconhecido", "cpp:art1: data-id desconhecido"]


def test_adr005_a_norma_pode_vir_em_mais_de_uma_secao():
    # A ordem é a dos tópicos do edital, não a da norma: o § 1º vai para outra seção da mesma
    # norma, fora do `data-id` do artigo, e continua conferido.
    inicio = HTML.index('<div class="paragrafo" data-id="art121.p1">')
    fim = HTML.index('<div class="paragrafo" data-id="art121.p2">')
    trecho = HTML[inicio:fim]
    html = HTML.replace(trecho, "").replace(
        "</body>", f'<div data-norma="cp">{trecho}</div></body>'
    )
    assert _conferir(html) == []
    texto = "o juiz pode reduzir a pena de um sexto a um terço."
    assert _conferir(html.replace(texto, "o juiz reduz a pena.")) != []


def test_divergencia_vira_linha():
    assert str(Divergencia("cp", "art121", "nó ausente")) == "cp:art121: nó ausente"
