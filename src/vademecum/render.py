"""Renderização do vade mecum em HTML a partir dos tópicos e dos recortes (ver ADR-006).

Etapa pura: recebe os tópicos, os recortes e os relatórios já lidos e devolve o HTML, sem I/O.
O texto legal sai literal nos campos `data-campo` dos nós `data-id`, no contrato que o
`conferir` lê (negocio/vade-mecum); tudo o mais (capa, sumário, saltos, notas, revogados) é
anotação, sem `data-id`. A ordem é a dos tópicos do edital (ADR-005), e a faixa do item segue o
ADR-004.
"""

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from html import escape
from typing import Any

from vademecum.modelo import Base, EntradaRelatorio, ErroFonte, Local, No, Relatorio, chave_de_texto
from vademecum.recorte import interpretar

ASSINATURA = "Lucas Vinha Teixeira · github.com/lucasvinha"
_COMPACTAS = ("redacao", "inclusao")  # viram a linha "Alterações" no fim do artigo
_NIVEIS_LOCAL = ("parte", "livro", "titulo", "capitulo", "secao", "subsecao", "rotulo_livre")
# Último segmento do `id`, para pôr o revogado entre os irmãos (`p2-A`, `pu`, `i6`, `a`).
_SEGMENTO = re.compile(r"p(?P<p>\d+)(?P<suf>(?:-[A-Z])*)|(?P<pu>pu)|i(?P<i>\d+)|(?P<a>[a-z])")
_CONFERENCIA = (
    "O texto legal foi copiado do recorte e conferido contra ele pelo conferir; as notas "
    "legislativas vêm da fonte, sem verificação independente."
)
_CSS = """
@page { size: A4; margin: 18mm 16mm 20mm;
  @bottom-left { content: "Lucas Vinha Teixeira · github.com/lucasvinha"; font-size: 8pt; }
  @bottom-right { content: "github.com/lucasvinha/vade-mecum-extractor · p. " counter(page);
    font-size: 8pt; } }
@page :first { @bottom-left { content: none; } @bottom-right { content: none; } }
body { font-family: Georgia, serif; line-height: 1.4; }
.capa, .sumario { break-after: page; }
.n1 { margin-left: 1.5em; } .n2 { margin-left: 3em; } .n3 { margin-left: 4.5em; }
.pena { background: #fdf4e3; border-left: 3px solid #d9a441; padding: 2px 6px; }
.nota, .alteracoes, .local, .salto, .revogado { color: #6b7280; font-size: 0.85em; }
"""


@dataclass
class _Entrada:
    """Uma posição do fluxo do item: artigo, artigo revogado (descarte) ou remissão."""

    norma: str
    artigo: No | None = None
    descarte: EntradaRelatorio | None = None
    remissao: No | None = None
    salto: str | None = None  # linha "fora do edital" que fecha esta entrada


@dataclass
class _Item:
    dados: Mapping[str, Any]
    entradas: list[_Entrada] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


# --- Fluxo -----------------------------------------------------------------------------------


def _numero(entrada: _Entrada) -> tuple[int, tuple[str, ...]]:
    if entrada.artigo is not None:
        return (entrada.artigo.numero or 0, entrada.artigo.sufixo)
    assert entrada.descarte is not None and entrada.descarte.id is not None
    return chave_de_texto(entrada.descarte.id.removeprefix("art"))


def _salto(anterior: tuple[int, tuple[str, ...]], seguinte: tuple[int, tuple[str, ...]]) -> str:
    """O buraco da numeração-base entre dois artigos; vazio no recuo ou sem buraco.

    O número-base do artigo com letra entra no buraco: 308 → 311-A dá "arts. 309 a 311".
    """
    inicio = anterior[0] + 1
    fim = seguinte[0] if seguinte[1] else seguinte[0] - 1
    if fim < inicio:
        return ""
    if fim == inicio:
        return f"art. {inicio} — fora do edital"
    return f"arts. {inicio} a {fim} — fora do edital"


def _fluxo(
    grupos: Sequence[Mapping[str, Any]], recortes: Mapping[str, tuple[Base, Relatorio]]
) -> list[tuple[Mapping[str, Any], list[_Item]]]:
    colocados: set[tuple[str, str]] = set()
    fluxo = []
    for grupo in grupos:
        norma = grupo.get("norma")
        if norma is not None and norma not in recortes:
            raise ErroFonte(f"falta o recorte da norma {norma!r}")
        base, relatorio = recortes[norma] if norma is not None else (None, Relatorio())
        artigos_rev = [
            e for e in relatorio.entradas if e.tipo == "descarte" and e.id and "." not in e.id
        ]
        itens = []
        for dados in grupo.get("itens", ()):
            item = _Item(dados)
            expressao = interpretar(dados["arts"]) if base is not None and "arts" in dados else ()
            textos = {parte.texto for parte in expressao}
            item.avisos = [
                e.texto for e in relatorio.entradas if e.tipo == "aviso" and e.origem in textos
            ]
            candidatos = [_Entrada(norma, artigo=a) for a in base.artigos] if base else []
            candidatos += [_Entrada(norma, descarte=d) for d in artigos_rev]
            for entrada in sorted(candidatos, key=_numero):
                if not any(p.inicio <= _numero(entrada) <= p.fim for p in expressao):  # ADR-004
                    continue
                chave = (norma, entrada.artigo.id if entrada.artigo else entrada.descarte.id)
                if chave in colocados and entrada.artigo is not None:
                    item.entradas.append(_Entrada(norma, remissao=entrada.artigo))
                elif chave not in colocados:
                    colocados.add(chave)
                    item.entradas.append(entrada)
            itens.append(item)
        fluxo.append((grupo, itens))
    for norma, (base, _) in recortes.items():
        for artigo in base.artigos:
            if (norma, artigo.id) not in colocados:
                raise ErroFonte(f"artigo do recorte fora dos tópicos: {norma}:{artigo.id}")
    anterior: _Entrada | None = None
    for _, itens in fluxo:
        for item in itens:
            for entrada in item.entradas:
                if entrada.remissao is not None:
                    continue
                if anterior is not None and anterior.norma == entrada.norma:
                    anterior.salto = _salto(_numero(anterior), _numero(entrada)) or None
                anterior = entrada
    return fluxo


# --- HTML ------------------------------------------------------------------------------------


def _e(texto: str) -> str:
    return escape(texto, quote=True)


def _ancora(norma: str, id_: str) -> str:
    return f"{norma}-{id_}"


def _ordem(id_: str) -> tuple[str, int, tuple[str, ...]] | None:
    casamento = _SEGMENTO.fullmatch(id_.rsplit(".", 1)[-1])
    if casamento is None:
        return None
    if casamento["p"]:
        return ("p", int(casamento["p"]), tuple(casamento["suf"].split("-")[1:]))
    if casamento["pu"]:
        return ("p", 0, ())
    if casamento["i"]:
        return ("i", int(casamento["i"]), ())
    return ("a", ord(casamento["a"]), ())


def _filhos_com_revogados(
    no: No, revogados: Sequence[EntradaRelatorio]
) -> list[No | EntradaRelatorio]:
    """Os filhos do nó com os revogados dele entre os irmãos, na ordem do rótulo."""
    filhos: list[No | EntradaRelatorio] = list(no.filhos)
    for revogado in revogados:
        ordem = _ordem(revogado.id or "")
        mesmos = [
            (i, o)
            for i, f in enumerate(filhos)
            if ordem is not None and (o := _ordem(f.id or "")) is not None and o[0] == ordem[0]
        ]
        menores = [i for i, o in mesmos if o < ordem]
        # Depois do último irmão menor do mesmo tipo; sem ele, antes do primeiro; sem irmão, no fim.
        posicao = len(filhos)
        if mesmos:
            posicao = menores[-1] + 1 if menores else mesmos[0][0]
        filhos.insert(posicao, revogado)
    return filhos


def _revogados_por_pai(artigo: No, relatorio: Relatorio) -> dict[str, list[EntradaRelatorio]]:
    """Descartes do artigo, cada um sob o ancestral mais próximo que está no recorte."""
    ids = {no.id for no in _nos((artigo,))}
    por_pai: dict[str, list[EntradaRelatorio]] = {}
    for entrada in relatorio.entradas:
        if entrada.tipo != "descarte" or not entrada.id or "." not in entrada.id:
            continue
        pai = entrada.id.rsplit(".", 1)[0]
        while "." in pai and pai not in ids:
            pai = pai.rsplit(".", 1)[0]
        if pai in ids:
            por_pai.setdefault(pai, []).append(entrada)
    return por_pai


def _nos(nos: Sequence[No]) -> Iterator[No]:
    for no in nos:
        yield no
        yield from _nos(no.filhos)


def _notas_do_no(no: No) -> str:
    """As notas que não são de redação nem de inclusão, coladas ao dispositivo, uma vez cada."""
    brutos = dict.fromkeys(
        n.bruto for n in no.notas if n.tipo not in _COMPACTAS or n.norma is None or n.ano is None
    )
    return "".join(f' <span class="nota">{_e(b)}</span>' for b in brutos)


def _alteracoes(artigo: No) -> str:
    """Linha "Alterações" do artigo: norma/ano das notas de redação e inclusão, por ano."""
    pares = dict.fromkeys(
        (n.ano, n.norma)
        for no in _nos((artigo,))
        for n in no.notas
        if n.tipo in _COMPACTAS and n.norma is not None and n.ano is not None
    )
    if not pares:
        return ""
    texto = " · ".join(f"{norma}/{ano}" for ano, norma in sorted(pares, key=lambda p: p[0]))
    return f'<p class="alteracoes">Alterações: {_e(texto)}</p>'


def _campo(nome: str, valor: str | None, classe: str = "", tag: str = "span") -> str:
    if not valor:
        return ""
    atributo = f' class="{classe}"' if classe else ""
    return f'<{tag}{atributo} data-campo="{nome}">{_e(valor)}</{tag}>'


def _dispositivo(
    no: No, nivel: int, por_pai: Mapping[str, Sequence[EntradaRelatorio]]
) -> list[str]:
    linhas = []
    if no.tipo == "pena":
        linhas.append(
            f'<div class="pena n{nivel}" data-id="{_e(no.id)}">'
            f'<span class="rotulo-pena">PENA</span> {_campo("rotulo", no.rotulo)}'
            f"{_campo('texto', no.texto)}{_notas_do_no(no)}</div>"
        )
    else:
        linhas.append(
            f'<div class="disp {no.tipo} n{nivel}" data-id="{_e(no.id)}">'
            f"{_campo('rubrica', no.rubrica, 'rubrica', 'p')}"
            f'<p class="linha">{_campo("rotulo", no.rotulo, "marca")} '
            f"{_campo('texto', no.texto, 'conteudo')}{_notas_do_no(no)}</p></div>"
        )
    for filho in _filhos_com_revogados(no, por_pai.get(no.id, ())):
        linhas.extend(_filho(filho, nivel + 1, por_pai))
    return linhas


def _revogado(entrada: EntradaRelatorio, nivel: int) -> str:
    rubrica = f" <em>{_e(entrada.rubrica)}</em>" if entrada.rubrica else ""
    # A nota da revogação; as de redação e inclusão de antes dela ficam só no relatório.
    proprias = [n for n in entrada.notas if n.tipo not in _COMPACTAS] or list(entrada.notas)
    notas = " ".join(_e(n.bruto) for n in proprias)
    return (
        f'<p class="revogado n{nivel}"><span class="marca">{_e(entrada.rotulo or "")}</span> '
        f'<span class="etiqueta">{_e((entrada.motivo or "").upper())}</span>{rubrica} {notas}</p>'
    )


def _filho(filho: No | EntradaRelatorio, nivel: int, por_pai) -> list[str]:
    if isinstance(filho, EntradaRelatorio):
        return [_revogado(filho, nivel)]
    return _dispositivo(filho, nivel, por_pai)


def _artigo(norma: str, artigo: No, relatorio: Relatorio) -> list[str]:
    por_pai = _revogados_por_pai(artigo, relatorio)
    linhas = [
        f'<article class="artigo" id="{_ancora(norma, artigo.id)}" data-id="{_e(artigo.id)}">',
        _campo("rubrica", artigo.rubrica, "rubrica", "h4"),
        f'<p class="caput">{_campo("rotulo", artigo.rotulo, "num-art")} '
        f"{_campo('texto', artigo.texto)}{_notas_do_no(artigo)}</p>",
    ]
    for filho in _filhos_com_revogados(artigo, por_pai.get(artigo.id, ())):
        linhas.extend(_filho(filho, 1, por_pai))
    linhas += [_alteracoes(artigo), "</article>"]
    return [linha for linha in linhas if linha]


def _local(local: Local | None) -> str:
    if local is None:
        return ""
    niveis = [getattr(local, nome) for nome in _NIVEIS_LOCAL if getattr(local, nome)]
    return f'<p class="local">{_e(" · ".join(niveis))}</p>' if niveis else ""


def _item(item: _Item, recortes: Mapping[str, tuple[Base, Relatorio]]) -> list[str]:
    dados = item.dados
    selo = (
        ' <span class="selo-oj">cobrado para Oficial de Justiça</span>' if dados.get("oj") else ""
    )
    linhas = [
        f'<section class="item" id="{_e(dados["id"].replace(":", "-"))}">',
        f"<h3>{_e(dados['rubrica'])}{selo}</h3>",
    ]
    if dados.get("nota"):
        linhas.append(f'<p class="aviso-item">{_e(dados["nota"])}</p>')
    linhas += [f'<p class="aviso-relatorio">{_e(aviso)}</p>' for aviso in item.avisos]
    local_atual = None
    for entrada in item.entradas:
        if entrada.remissao is not None:
            rotulo = (entrada.remissao.rotulo or "").replace("Art.", "art.", 1)
            href = _ancora(entrada.norma, entrada.remissao.id)
            linhas.append(f'<p class="remissao"><a href="#{href}">ver {_e(rotulo)}, acima</a></p>')
            continue
        if entrada.artigo is not None:
            local = _local(entrada.artigo.local)
            if local and local != local_atual:
                linhas.append(local)
                local_atual = local
            linhas += _artigo(entrada.norma, entrada.artigo, recortes[entrada.norma][1])
        else:
            assert entrada.descarte is not None
            linhas.append(_revogado(entrada.descarte, 0))
        if entrada.salto:
            linhas.append(f'<p class="salto">· · · {_e(entrada.salto)} · · ·</p>')
    linhas.append("</section>")
    return linhas


def _sumario(fluxo) -> list[str]:
    linhas = ['<nav class="sumario">', "<h2>Sumário</h2>"]
    for numero, (grupo, itens) in enumerate(fluxo, start=1):
        linhas.append(f'<p class="item h"><a href="#g{numero}">{_e(grupo["titulo"])}</a></p>')
        for item in itens:
            ancora = item.dados["id"].replace(":", "-")
            linhas.append(
                f'<p class="item i"><a href="#{_e(ancora)}">{_e(item.dados["rubrica"])}</a></p>'
            )
            for entrada in item.entradas:
                if entrada.artigo is None:
                    continue
                texto = " — ".join(filter(None, (entrada.artigo.rotulo, entrada.artigo.rubrica)))
                href = _ancora(entrada.norma, entrada.artigo.id)
                linhas.append(f'<p class="item"><a href="#{href}">{_e(texto)}</a></p>')
    linhas.append("</nav>")
    return linhas


def _capa(topicos, materia, recortes, avisos_sem_item: Sequence[str]) -> list[str]:
    normas = [base.norma.titulo or base.norma.id for base, _ in recortes.values()]
    avisos = [
        f"Texto da norma {base.norma.id} capturado do Planalto em {base.norma.capturado_em[:10]}."
        for base, _ in recortes.values()
    ]
    avisos += [_CONFERENCIA, *avisos_sem_item]
    return [
        '<section class="capa">',
        f'<p class="selo">{_e(" · ".join(normas))}</p>',
        "<h1>VADE MECUM</h1>",
        f'<p class="sub">{_e(materia["nome"])}</p>',
        f'<p class="edital">{_e(topicos.get("edital", ""))}</p>',
        '<div class="aviso"><p><strong>Avisos de uso</strong></p><ul>',
        *(f"<li>{_e(aviso)}</li>" for aviso in avisos),
        "</ul></div>",
        f'<p class="assinatura">{_e(ASSINATURA)}</p>',
        "</section>",
    ]


def renderizar(
    topicos: Mapping[str, Any], materia: str, recortes: Sequence[tuple[Base, Relatorio]]
) -> str:
    """O HTML do vade mecum da `materia`, com o texto legal dos `recortes` (ADR-006).

    `recortes` traz cada recorte com o seu relatório, de onde saem os revogados e os avisos.
    `ErroFonte` quando a matéria não existe, falta o recorte de uma norma dos grupos ou sobra
    artigo do recorte que nenhum item cobre (RNF04).
    """
    materias = [m for m in topicos.get("materias", ()) if m.get("id") == materia]
    if not materias:
        raise ErroFonte(f"matéria inexistente nos tópicos: {materia!r}")
    por_norma = {base.norma.id: (base, relatorio) for base, relatorio in recortes}
    fluxo = _fluxo(materias[0].get("grupos", ()), por_norma)
    com_item = {aviso for _, itens in fluxo for item in itens for aviso in item.avisos}
    sem_item = [
        e.texto
        for _, relatorio in por_norma.values()
        for e in relatorio.entradas
        if e.tipo == "aviso" and e.texto not in com_item
    ]
    corpo = []
    for numero, (grupo, itens) in enumerate(fluxo, start=1):
        norma = grupo.get("norma")
        atributo = f' data-norma="{_e(norma)}"' if norma else ""
        corpo.append(f'<section class="grupo" id="g{numero}"{atributo}>')
        corpo.append(f"<h2>{_e(grupo['titulo'])}</h2>")
        for item in itens:
            corpo += _item(item, por_norma)
        corpo.append("</section>")
    linhas = [
        "<!DOCTYPE html>",
        '<html lang="pt-BR">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>Vade mecum — {_e(materias[0]['nome'])}</title>",
        f"<style>{_CSS}</style>",
        "</head>",
        "<body>",
        *_capa(topicos, materias[0], por_norma, sem_item),
        *_sumario(fluxo),
        '<main class="corpo">',
        *corpo,
        "</main>",
        "</body>",
        "</html>",
    ]
    return "\n".join(linhas) + "\n"
