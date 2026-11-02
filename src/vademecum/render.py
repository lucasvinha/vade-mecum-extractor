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
from importlib.resources import files
from typing import Any

from vademecum.curadoria import (
    CATEGORIAS,
    CelulaPena,
    Curadoria,
    Dispositivo,
    Marca,
    Quadro,
    exigir_normas_distintas,
)
from vademecum.modelo import Base, EntradaRelatorio, ErroFonte, Local, No, Relatorio, chave_de_texto
from vademecum.recorte import interpretar

ASSINATURA = "Lucas Vinha Teixeira · github.com/lucasvinha"
_COMPACTAS = ("redacao", "inclusao")  # viram a linha "Alterações" no fim do artigo
_NIVEIS_LOCAL = ("parte", "livro", "titulo", "capitulo", "secao", "subsecao", "rotulo_livre")
# Último segmento do `id`, para pôr o revogado entre os irmãos (`p2-A`, `pu`, `i6`, `a`).
_SEGMENTO = re.compile(r"p(?P<p>\d+)(?P<suf>(?:-[A-Z])*)|(?P<pu>pu)|i(?P<i>\d+)|(?P<a>[a-z])")
_APOIO = "Material de apoio elaborado para estudo — não é texto de lei."
# Amostra e descrição de cada categoria de marca (estilo.md).
_LEGENDA = {
    "verbo": ("conduta nuclear", "o verbo do tipo"),
    "sujeito": ("sujeito", "quem pode praticar, a qualidade exigida"),
    "especializante": ("elemento especializante", "o detalhe que separa o tipo do vizinho"),
    "quantidade": ("quantidade", "prazos, frações e quantidades"),
    "condicao": ("condição", "subsidiariedade e procedibilidade"),
}
_DATA_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_CONFERENCIA = (
    "O texto legal foi copiado do recorte e conferido contra ele pelo conferir; as notas "
    "legislativas vêm da fonte, sem verificação independente."
)
# Recurso do pacote, lido uma vez: o HTML leva o CSS embutido, sem arquivo externo (INSTRUCOES).
# `read_text` troca CRLF por LF, e o HTML sai igual em qualquer checkout (RNF03).
_CSS = files("vademecum").joinpath("estilo", "vade-mecum.css").read_text(encoding="utf-8")


@dataclass
class _Entrada:
    """Uma posição do fluxo do item: artigo, artigo revogado (descarte) ou remissão."""

    norma: str
    artigo: No | None = None
    descarte: EntradaRelatorio | None = None
    remissao: No | None = None
    salto: str | None = None  # linha "fora do edital" que fecha esta entrada


@dataclass(frozen=True)
class _Anotacoes:
    """A curadoria de uma norma, pelo `id` do nó (sem o prefixo `<norma>:`)."""

    dispositivos: Mapping[str, Dispositivo] = field(default_factory=dict)
    quadros: Mapping[str, Sequence[Quadro]] = field(default_factory=dict)

    def marcas(self, id_: str) -> Sequence[Marca]:
        dispositivo = self.dispositivos.get(id_)
        return dispositivo.marcas if dispositivo else ()

    def depois(self, id_: str) -> list[str]:
        """As atenções e os quadros que vêm logo depois do nó."""
        dispositivo = self.dispositivos.get(id_)
        atencoes = dispositivo.atencao if dispositivo else ()
        linhas = [f'<aside class="atencao">{_e(texto)}</aside>' for texto in atencoes]
        for quadro in self.quadros.get(id_, ()):
            linhas += _quadro(quadro)
        return linhas


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

    O número-base do artigo com letra entra no buraco: 308 → 311-A dá "arts. 309 a 311". No mesmo
    número, o buraco é o das letras: 313 → 313-B dá "art. 313-A".
    """
    if anterior[0] == seguinte[0]:
        return _salto_de_letra(anterior[0], anterior[1], seguinte[1])
    inicio = anterior[0] + 1
    fim = seguinte[0] if seguinte[1] else seguinte[0] - 1
    if fim < inicio:
        return ""
    if fim == inicio:
        return f"art. {inicio} — fora do edital"
    return f"arts. {inicio} a {fim} — fora do edital"


def _salto_de_letra(numero: int, anterior: tuple[str, ...], seguinte: tuple[str, ...]) -> str:
    """As letras puladas entre dois artigos do mesmo número; vazio sem buraco.

    Só a primeira letra conta: o sufixo composto (`359-M-A`) não abre buraco aqui.
    """
    if len(anterior) > 1 or len(seguinte) != 1:
        return ""
    inicio = chr(ord(anterior[0]) + 1) if anterior else "A"
    fim = chr(ord(seguinte[0]) - 1)
    if fim < inicio:
        return ""
    if fim == inicio:
        return f"art. {numero}-{inicio} — fora do edital"
    return f"arts. {numero}-{inicio} a {numero}-{fim} — fora do edital"


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


def _marcado(texto: str, marcas: Sequence[Marca]) -> str:
    """O texto escapado, com cada marca num `<mark>`: o texto conferido não muda (ADR-006)."""
    partes, posicao = [], 0
    for marca in marcas:
        partes.append(_e(texto[posicao : marca.inicio]))
        partes.append(f'<mark class="hl-{marca.cat}">{_e(texto[marca.inicio : marca.fim])}</mark>')
        posicao = marca.fim
    partes.append(_e(texto[posicao:]))
    return "".join(partes)


def _campo(
    nome: str, valor: str | None, classe: str = "", tag: str = "span", marcas: Sequence[Marca] = ()
) -> str:
    if not valor:
        return ""
    atributo = f' class="{classe}"' if classe else ""
    return f'<{tag}{atributo} data-campo="{nome}">{_marcado(valor, marcas)}</{tag}>'


@dataclass(frozen=True)
class _Contexto:
    """O que o artigo em curso precisa: os revogados por pai e a curadoria da norma."""

    por_pai: Mapping[str, Sequence[EntradaRelatorio]]
    anotacoes: _Anotacoes


def _dispositivo(no: No, nivel: int, ctx: _Contexto) -> list[str]:
    marcas = ctx.anotacoes.marcas(no.id)
    if no.tipo == "pena":
        linhas = [
            f'<div class="pena n{nivel}" data-id="{_e(no.id)}">'
            f'<span class="rotulo-pena">PENA</span> {_campo("rotulo", no.rotulo)}'
            f"{_campo('texto', no.texto, marcas=marcas)}{_notas_do_no(no)}</div>"
        ]
    else:
        linhas = [
            f'<div class="disp {no.tipo} n{nivel}" data-id="{_e(no.id)}">'
            f"{_campo('rubrica', no.rubrica, 'rubrica', 'p')}"
            f'<p class="linha">{_campo("rotulo", no.rotulo, "marca")} '
            f"{_campo('texto', no.texto, 'conteudo', marcas=marcas)}{_notas_do_no(no)}</p></div>"
        ]
    for filho in _filhos_com_revogados(no, ctx.por_pai.get(no.id, ())):
        linhas.extend(_filho(filho, nivel + 1, ctx))
    return linhas + ctx.anotacoes.depois(no.id)


def _revogado(entrada: EntradaRelatorio, nivel: int) -> str:
    rubrica = f" <em>{_e(entrada.rubrica)}</em>" if entrada.rubrica else ""
    # A nota da revogação; as de redação e inclusão de antes dela ficam só no relatório.
    proprias = [n for n in entrada.notas if n.tipo not in _COMPACTAS] or list(entrada.notas)
    notas = " ".join(_e(n.bruto) for n in proprias)
    return (
        f'<p class="revogado n{nivel}"><span class="marca">{_e(entrada.rotulo or "")}</span> '
        f'<span class="etiqueta">{_e((entrada.motivo or "").upper())}</span>{rubrica} {notas}</p>'
    )


def _filho(filho: No | EntradaRelatorio, nivel: int, ctx: _Contexto) -> list[str]:
    if isinstance(filho, EntradaRelatorio):
        return [_revogado(filho, nivel)]
    return _dispositivo(filho, nivel, ctx)


def _artigo(norma: str, artigo: No, relatorio: Relatorio, anotacoes: _Anotacoes) -> list[str]:
    ctx = _Contexto(_revogados_por_pai(artigo, relatorio), anotacoes)
    texto = _campo("texto", artigo.texto, marcas=anotacoes.marcas(artigo.id))
    linhas = [
        f'<article class="artigo" id="{_ancora(norma, artigo.id)}" data-id="{_e(artigo.id)}">',
        _campo("rubrica", artigo.rubrica, "rubrica", "h4"),
        f'<p class="caput">{_campo("rotulo", artigo.rotulo, "num-art")} '
        f"{texto}{_notas_do_no(artigo)}</p>",
    ]
    for filho in _filhos_com_revogados(artigo, ctx.por_pai.get(artigo.id, ())):
        linhas.extend(_filho(filho, 1, ctx))
    linhas += [_alteracoes(artigo), *anotacoes.depois(artigo.id), "</article>"]
    return [linha for linha in linhas if linha]


def _quadro(quadro: Quadro) -> list[str]:
    """Quadro comparativo; a pena da célula ancorada já vem conferida da curadoria."""
    cabecalho = "".join(f"<th>{_e(coluna)}</th>" for coluna in quadro.colunas)
    linhas = [
        '<div class="quadro">',
        f"<h3>{_e(quadro.titulo)}</h3>",
        f"<table><thead><tr>{cabecalho}</tr></thead><tbody>",
    ]
    for linha in quadro.linhas:
        celulas = "".join(
            f'<td class="pena-celula">{_e(c.texto)}</td>'
            if isinstance(c, CelulaPena)
            else f"<td>{_e(c)}</td>"
            for c in linha
        )
        linhas.append(f"<tr>{celulas}</tr>")
    linhas.append("</tbody></table>")
    if quadro.nota:
        linhas.append(f'<p class="rodape">{_e(quadro.nota)}</p>')
    return [*linhas, f'<p class="apoio">{_APOIO}</p>', "</div>"]


def _local(local: Local | None) -> str:
    if local is None:
        return ""
    niveis = [getattr(local, nome) for nome in _NIVEIS_LOCAL if getattr(local, nome)]
    return f'<p class="local">{_e(" · ".join(niveis))}</p>' if niveis else ""


def _item(
    item: _Item,
    recortes: Mapping[str, tuple[Base, Relatorio]],
    anotacoes: Mapping[str, _Anotacoes],
) -> list[str]:
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
            relatorio = recortes[entrada.norma][1]
            linhas += _artigo(entrada.norma, entrada.artigo, relatorio, anotacoes[entrada.norma])
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


def _legenda() -> list[str]:
    linhas = ['<section class="legenda">', "<h2>Como ler os destaques</h2>"]
    for cat in CATEGORIAS:
        amostra, descricao = _LEGENDA[cat]
        linhas.append(f'<p><mark class="hl-{cat}">{amostra}</mark> — {descricao}</p>')
    return [
        *linhas,
        '<p><span class="pena-amostra">PENA</span> — caixa âmbar: a pena do dispositivo</p>',
        '<p class="apoio">Quadros comparativos e pontos de atenção são material de apoio elaborado'
        " para estudo — não são texto de lei.</p>",
        "</section>",
    ]


def _data(gerado_em: str) -> str:
    casamento = _DATA_ISO.fullmatch(gerado_em)
    return f"{casamento[3]}/{casamento[2]}/{casamento[1]}" if casamento else gerado_em


def _capa(
    topicos, materia, recortes, avisos_sem_item: Sequence[str], curadoria: Curadoria | None
) -> list[str]:
    normas = [base.norma.titulo or base.norma.id for base, _ in recortes.values()]
    avisos = [
        f"Texto da norma {base.norma.id} capturado do Planalto em {base.norma.capturado_em[:10]}."
        for base, _ in recortes.values()
    ]
    avisos.append(_CONFERENCIA)
    if curadoria is not None:
        avisos += curadoria.avisos_capa
    avisos += avisos_sem_item
    # A data vem da curadoria, nunca do relógio (RNF03); sem curadoria, a capa sai sem data.
    datas = (
        [f'<p class="edital">Gerado em {_e(_data(curadoria.gerado_em))}</p>'] if curadoria else []
    )
    return [
        '<section class="capa">',
        f'<p class="selo">{_e(" · ".join(normas))}</p>',
        "<h1>VADE MECUM</h1>",
        f'<p class="sub">{_e(materia["nome"])}</p>',
        f'<p class="edital">{_e(topicos.get("edital", ""))}</p>',
        *datas,
        '<div class="aviso"><p><strong>Avisos de uso</strong></p><ul>',
        *(f"<li>{_e(aviso)}</li>" for aviso in avisos),
        "</ul></div>",
        f'<p class="assinatura">{_e(ASSINATURA)}</p>',
        "</section>",
    ]


def _anotacoes(
    curadoria: Curadoria | None, recortes: Mapping[str, tuple[Base, Relatorio]]
) -> dict[str, _Anotacoes]:
    """A curadoria repartida por norma; a chave que não é nó dos recortes é erro (RNF04)."""
    if curadoria is None:
        return {norma: _Anotacoes() for norma in recortes}
    chaves = {f"{n}:{no.id}" for n, (base, _) in recortes.items() for no in _nos(base.artigos)}
    soltas = [chave for chave in curadoria.dispositivos if chave not in chaves]
    soltas += [q.depois_de for q in curadoria.quadros if q.depois_de not in chaves]
    if soltas:
        raise ErroFonte(f"curadoria fora dos recortes: {', '.join(soltas)}")
    anotacoes = {}
    for norma in recortes:
        prefixo = f"{norma}:"
        quadros: dict[str, list[Quadro]] = {}
        for quadro in curadoria.quadros:
            if quadro.depois_de.startswith(prefixo):
                quadros.setdefault(quadro.depois_de.removeprefix(prefixo), []).append(quadro)
        dispositivos = {
            chave.removeprefix(prefixo): dispositivo
            for chave, dispositivo in curadoria.dispositivos.items()
            if chave.startswith(prefixo)
        }
        anotacoes[norma] = _Anotacoes(dispositivos, quadros)
    return anotacoes


def renderizar(
    topicos: Mapping[str, Any],
    materia: str,
    recortes: Sequence[tuple[Base, Relatorio]],
    curadoria: Curadoria | None = None,
) -> str:
    """O HTML do vade mecum da `materia`, com o texto legal dos `recortes` (ADR-006).

    `recortes` traz cada recorte com o seu relatório, de onde saem os revogados e os avisos.
    A `curadoria`, já validada por `validar_curadoria`, põe as marcas, as atenções, os quadros,
    a legenda e os avisos e a data da capa. `ErroFonte` quando a matéria não existe, falta o
    recorte de uma norma dos grupos ou ele vem repetido, sobra artigo do recorte que nenhum item
    cobre, a curadoria é de outra matéria ou cita nó fora dos recortes (RNF04).
    """
    materias = [m for m in topicos.get("materias", ()) if m.get("id") == materia]
    if not materias:
        raise ErroFonte(f"matéria inexistente nos tópicos: {materia!r}")
    if curadoria is not None and curadoria.materia != materia:
        raise ErroFonte(f"curadoria da matéria {curadoria.materia!r}, e não de {materia!r}")
    exigir_normas_distintas([base for base, _ in recortes])
    por_norma = {base.norma.id: (base, relatorio) for base, relatorio in recortes}
    fluxo = _fluxo(materias[0].get("grupos", ()), por_norma)
    anotacoes = _anotacoes(curadoria, por_norma)
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
        # O título fica fora das colunas da impressão, para não ficar sozinho no pé da página.
        corpo.append(f'<h2>{_e(grupo["titulo"])}</h2>\n<div class="colunas">')
        for item in itens:
            corpo += _item(item, por_norma, anotacoes)
        corpo.append("</div>\n</section>")
    linhas = [
        "<!DOCTYPE html>",
        '<html lang="pt-BR">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>Vade mecum — {_e(materias[0]['nome'])}</title>",
        f"<style>{_CSS}</style>",
        "</head>",
        "<body>",
        *_capa(topicos, materias[0], por_norma, sem_item, curadoria),
        *_sumario(fluxo),
        *(_legenda() if curadoria is not None else ()),
        '<main class="corpo">',
        *corpo,
        "</main>",
        "</body>",
        "</html>",
    ]
    return "\n".join(linhas) + "\n"
