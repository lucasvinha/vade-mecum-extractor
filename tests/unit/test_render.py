"""Render do vade mecum: texto legal no contrato do `conferir`, saltos e notas (ADR-006)."""

import dataclasses
import re
from pathlib import Path

import pytest

from vademecum.conferencia import conferir
from vademecum.curadoria import CATEGORIAS, validar_curadoria
from vademecum.modelo import (
    EntradaRelatorio,
    ErroFonte,
    Nota,
    Relatorio,
    de_json,
    relatorio_de_json,
)
from vademecum.recorte import interpretar, recortar
from vademecum.render import renderizar

SNAPSHOTS = Path(__file__).resolve().parents[1] / "fixtures" / "snapshots"
BASE = de_json((SNAPSHOTS / "cp_enxertos.json").read_text(encoding="utf-8"))
RELATORIO = relatorio_de_json(
    (SNAPSHOTS / "cp_enxertos.relatorio.json").read_text(encoding="utf-8")
)


def _topicos(*grupos):
    """Tópicos de teste: cada grupo é uma lista de itens `(arts, extras)` da norma `cp`."""
    return {
        "schema": "topicos-oj/2",
        "edital": "Edital de teste",
        "materias": [
            {
                "id": "penal",
                "nome": "Direito Penal",
                "grupos": [
                    {
                        "titulo": f"Grupo {g}",
                        "norma": "cp",
                        "itens": [
                            {"id": f"penal:g{g}i{i}", "rubrica": f"Item {g}.{i}", "arts": arts}
                            | extras
                            for i, (arts, extras) in enumerate(itens, start=1)
                        ],
                    }
                    for g, itens in enumerate(grupos, start=1)
                ],
            }
        ],
    }


def _render(*grupos, base=BASE, relatorio=RELATORIO):
    return renderizar(_topicos(*grupos), "penal", [(base, relatorio)])


def _so(expressao):
    """O recorte do snapshot só com os artigos da expressão."""
    return recortar(BASE, interpretar(expressao), (), Relatorio())


def _saltos(html):
    return re.findall(r'<p class="salto">· · · (.*?) · · ·</p>', html)


def _base_com(*numeros):
    """Base com cópias do art. 78 renumeradas: `(numero, sufixo)` cada."""
    modelo = BASE.artigos[0]
    artigos = tuple(
        dataclasses.replace(modelo, id=f"art{n}{''.join('-' + s for s in suf)}", numero=n,
                            sufixo=suf, filhos=())
        for n, suf in numeros
    )  # fmt: skip
    return dataclasses.replace(BASE, artigos=artigos)


def test_adr006_texto_legal_passa_no_conferir():
    html = _render([("78", {})], [("121 a 130", {"oj": True, "nota": "Nota do item"})])
    assert conferir([BASE], html) == ()
    assert "cobrado para Oficial de Justiça" in html
    assert '<p class="aviso-item">Nota do item</p>' in html


def test_adr006_render_deterministico():
    assert _render([("78; 121 a 130", {})]) == _render([("78; 121 a 130", {})])


def test_adr006_salto_na_troca_de_grupo_fecha_o_grupo_anterior():
    html = _render([("78", {})], [("121 a 130", {})])
    assert _saltos(html) == ["arts. 79 a 120 — fora do edital"]
    assert html.index("arts. 79 a 120") < html.index('<section class="grupo" id="g2"')


def test_adr006_recuo_nao_gera_salto():
    assert _saltos(_render([("121 a 130", {})], [("78", {})])) == []


def test_adr006_artigo_com_letra_poe_o_numero_base_no_salto():
    # 308 → 311-A: o 311 também está fora do edital.
    base = _base_com((306, ()), (308, ()), (311, ("A",)), (311, ("B",)), (312, ()))
    html = _render([("306 a 312", {})], base=base)
    assert _saltos(html) == ["art. 307 — fora do edital", "arts. 309 a 311 — fora do edital"]


def test_adr006_artigo_coberto_por_dois_itens_vira_remissao():
    base = _so("121")
    html = _render([("121", {}), ("121", {})], base=base)
    assert html.count('data-id="art121"') == 1
    assert '<a href="#cp-art121">ver art. 121, acima</a>' in html
    assert conferir([base], html) == ()


def test_adr006_revogados_entre_os_irmaos_na_ordem_do_rotulo():
    html = _render([("121", {})], base=_so("121"))
    i5, vi, i7 = (
        html.index(s) for s in ('data-id="art121.p2.i5"', ">VI<", 'data-id="art121.p2.i7"')
    )
    assert i5 < vi < i7
    p2, p2a, p2b = (
        html.index(s) for s in ('data-id="art121.p2"', ">§ 2º-A<", 'data-id="art121.p2-B"')
    )
    assert p2 < p2a < p2b
    assert "REVOGADO</span> <em>Feminicídio</em>" in html


def test_adr006_notas_compactas_no_fim_do_artigo():
    # Redação e inclusão viram norma/ano, uma vez cada, por ano; vigência fica no dispositivo.
    html = _render([("121", {})], base=_so("121"))
    linha = re.search(r'<p class="alteracoes">Alterações: (.*?)</p>', html)[1]
    assert linha.startswith("Lei nº 6.416/1977 · Lei nº 10.741/2003 · Lei nº 12.720/2012")
    assert linha.count("Lei nº 14.344/2022") == 1
    assert "(Incluído pela" not in html
    assert '<span class="nota">(Vigência)</span>' in html


def test_adr006_notas_do_mesmo_ano_na_ordem_do_texto():
    artigo = dataclasses.replace(
        BASE.artigos[0],
        notas=(
            Nota("redacao", "(x)", "Lei 12.550", 2011),
            Nota("redacao", "(y)", "Lei nº 7.209", 1984),
            Nota("inclusao", "(z)", "Lei nº 12.403", 2011),
        ),
        filhos=(),
    )
    html = _render([("78", {})], base=dataclasses.replace(BASE, artigos=(artigo,)))
    assert "Alterações: Lei nº 7.209/1984 · Lei 12.550/2011 · Lei nº 12.403/2011" in html


def test_adr006_avisos_do_relatorio():
    # O aviso do recorte vai para o item da `origem`; o que não é de item nenhum vai para a capa.
    relatorio = Relatorio()
    for entrada in RELATORIO.entradas:
        relatorio.registrar(entrada)
    texto = "item do recorte sem artigo na base nem nos descartes: 121 a 130"
    relatorio.registrar(EntradaRelatorio(tipo="aviso", origem="121 a 130", texto=texto))
    html = _render([("78", {})], [("121 a 130", {})], relatorio=relatorio)
    capa = html[: html.index('<nav class="sumario">')]
    assert "título da norma não encontrado no cabeçalho (H17)" in capa
    item = html[html.index('id="penal-g2i1"') :]
    assert f'<p class="aviso-relatorio">{texto}</p>' in item
    assert texto not in capa


def test_adr006_sumario_com_links():
    html = _render([("121 a 130", {})], base=_so("121 a 130"))
    assert '<a href="#cp-art121">Art. 121 — Homicídio simples</a>' in html
    assert '<a href="#penal-g1i1">Item 1.1</a>' in html


def test_adr006_artigo_sem_item_e_erro():
    # RNF04: artigo do recorte que nenhum item cobre não some em silêncio.
    with pytest.raises(ErroFonte, match="artigo do recorte fora dos tópicos: cp:art121"):
        _render([("78", {})])


def test_adr006_materia_inexistente_e_erro():
    with pytest.raises(ErroFonte, match="matéria inexistente"):
        renderizar(_topicos([("78", {})]), "civil", [(BASE, RELATORIO)])


def test_adr006_css_do_pacote_embutido_sem_recurso_externo():
    html = _render([("78; 121 a 130", {})])
    css = re.search(r"<style>(.*)</style>", html, re.DOTALL)[1]
    assert ".pena {" in css and "@page :first" in css
    assert "\r" not in css
    assert not re.search(r"<link|<script|url\(", html)


def test_adr006_titulo_do_grupo_fora_das_colunas():
    html = _render([("78", {})], [("121 a 130", {})])
    assert html.count('<div class="colunas">') == 2
    assert '<h2>Grupo 2</h2>\n<div class="colunas">\n<section class="item"' in html


def _curadoria(base, **extra):
    dados = {"schema": "curadoria-vm/1", "edital": "oj26", "materia": "penal",
             "gerado_em": "2026-11-02", "dispositivos": {}} | extra  # fmt: skip
    validacao = validar_curadoria(dados, [base])
    assert validacao.erros == ()
    return validacao.curadoria


_QUADRO_121 = {
    "depois_de": "cp:art121.p1",
    "titulo": "Homicídio",
    "colunas": ["Dispositivo", "Pena"],
    "linhas": [
        ["Art. 121", {"pena": "cp:art121.pena1", "texto": "reclusão, 6 a 20 anos"}],
        ["Art. 121 (literal)", {"pena": "cp:art121.pena1"}],
    ],
    "nota": "Nota do quadro",
}


def test_adr006_marcas_dentro_do_campo_texto_passam_no_conferir():
    base = _so("121")
    marcas = [{"trecho": "Matar", "cat": "verbo"}, {"trecho": "alguem", "cat": "sujeito"}]
    curadoria = _curadoria(base, dispositivos={"cp:art121": {"marcas": marcas}})
    html = renderizar(_topicos([("121", {})]), "penal", [(base, RELATORIO)], curadoria)
    assert (
        '<span data-campo="texto"><mark class="hl-verbo">Matar</mark> '
        '<mark class="hl-sujeito">alguem</mark>:</span>'
    ) in html
    assert conferir([base], html) == ()


def test_adr006_atencao_e_quadro_logo_depois_do_no():
    base = _so("121")
    curadoria = _curadoria(
        base,
        dispositivos={"cp:art121.p1": {"atencao": ["Privilégio: <reduz> a pena"]}},
        quadros=[_QUADRO_121],
    )
    html = renderizar(_topicos([("121", {})]), "penal", [(base, RELATORIO)], curadoria)
    p1, aside, quadro, p2 = (
        html.index(s)
        for s in (
            'data-id="art121.p1"',
            '<aside class="atencao">Privilégio: &lt;reduz&gt; a pena</aside>',
            '<div class="quadro">',
            'data-id="art121.p2"',
        )
    )
    assert p1 < aside < quadro < p2
    assert "<th>Dispositivo</th><th>Pena</th>" in html
    # A pena resumida sai como está no quadro; a literal, com o texto do recorte.
    assert '<td class="pena-celula">reclusão, 6 a 20 anos</td>' in html
    assert '<td class="pena-celula">reclusão, de seis a vinte anos.</td>' in html
    assert '<p class="rodape">Nota do quadro</p>' in html
    assert "não é texto de lei" in html[quadro:p2]
    assert conferir([base], html) == ()


def test_adr006_capa_e_legenda_da_curadoria():
    base = _so("121")
    curadoria = _curadoria(base, avisos_capa=["Aviso da curadoria"])
    html = renderizar(_topicos([("121", {})]), "penal", [(base, RELATORIO)], curadoria)
    capa = html[: html.index('<nav class="sumario">')]
    assert "<li>Aviso da curadoria</li>" in capa
    assert '<p class="edital">Gerado em 02/11/2026</p>' in capa
    legenda = html[html.index('<section class="legenda">') : html.index('<main class="corpo">')]
    assert re.findall(r'class="hl-(\w+)"', legenda) == list(CATEGORIAS)
    assert "não são texto de lei" in legenda


def test_adr006_sem_curadoria_nao_ha_legenda_nem_data():
    # RNF03: sem curadoria, nada vem do relógio.
    html = _render([("121", {})], base=_so("121"))
    assert '<section class="legenda">' not in html
    assert "Gerado em" not in html


def test_adr006_curadoria_fora_dos_recortes_e_erro():
    # RNF04: o quadro ancorado num nó que não sai no HTML não some em silêncio.
    curadoria = _curadoria(BASE, quadros=[_QUADRO_121])
    with pytest.raises(ErroFonte, match=r"curadoria fora dos recortes: cp:art121\.p1"):
        renderizar(_topicos([("78", {})]), "penal", [(_so("78"), RELATORIO)], curadoria)
