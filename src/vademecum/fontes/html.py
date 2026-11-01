"""Leitor do HTML do Planalto: `.mht` do navegador ou `.htm` → `FonteLida` (ver negocio/fontes).

Único lugar, com a `cli.py`, que lê arquivo (PADRAO_OURO). A unidade de saída é a linha lógica,
não o parágrafo HTML (H4).
"""

import email
import email.policy
import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email.headerregistry import DateHeader
from email.message import EmailMessage
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from vademecum.modelo import EntradaRelatorio, ErroFonte, FonteLida, LinhaFonte, Relatorio

_EXTENSOES_MHT = frozenset({".mht", ".mhtml"})
_EXTENSOES_HTM = frozenset({".htm", ".html"})

# H1: o `.htm` do Planalto não declara charset; quem declara no `.mht` é o `<meta>` do navegador
# (`<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">`).
_CHARSET_PADRAO = "windows-1252"
_META_CHARSET = re.compile(rb"<meta[^>]*?charset\s*=\s*[\"']?([\w-]+)", re.IGNORECASE)

# RF04, H3: quebra só nestes elementos; o `\n` do código-fonte é espaço como outro qualquer.
_BLOCOS = frozenset(
    {"p", "div", "blockquote", "tr", "center", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
)
_FORA_DO_TEXTO = frozenset({"head", "script", "style"})
_NEGRITO = frozenset({"b", "strong"})  # H5, H6
# H6: o CP também põe negrito só pelo `style` (`font-weight: 700`, rubrica do art. 311-A) e o
# tira dentro do `<b>` (`font-weight: normal`, art. 298, parágrafo único).
_FONT_WEIGHT = re.compile(r"font-weight\s*:\s*(\w+)", re.IGNORECASE)
_PESOS_NEGRITO = frozenset({"bold", "bolder"})
# H5: o CP também centraliza só pelo `style` (`text-align:center`, no CAPÍTULO V do Título X).
_TEXT_ALIGN_CENTRO = re.compile(r"text-align\s*:\s*center", re.IGNORECASE)
# H8: tachado é redação que não vale mais. Linha cujo resto, fora do tachado, é vazio ou só notas
# sai inteira: `<strike>Art. 4° Os agentes…</strike> (Revogado pela Lei nº 14.230, de 2021)`
# (Lei 8.429) e `(Redação dada pela Lei nº 12.403, de 2011).` (CPP, art. 336) são as notas reais.
_TACHADO = frozenset({"strike", "s", "del"})
# H8: o tachado também vem só pelo CSS, em qualquer ancestral: `text-decoration:line-through`
# (CPC, art. 63, § 1º antigo) e `text-decoration: none line-through` (Lei 8.429, art. 17, § 3º).
_LINE_THROUGH = re.compile(r"text-decoration\s*:[^;]*\bline-through", re.IGNORECASE)
_SO_NOTAS = re.compile(r"(?: ?\([^()]*\)\.?)*")
_FIM_DE_BLOCO = object()
_ESPACO = re.compile(r"\s+")  # em `str`, `\s` inclui o `\xa0` do `&nbsp;`


def ler_html(caminho: Path, relatorio: Relatorio) -> FonteLida:
    """Lê a fonte HTML local e devolve as linhas lógicas na ordem do texto.

    `relatorio` recebe o texto da leitura que não vira linha (RNF04). Levanta `ErroFonte` para
    arquivo inexistente, extensão não suportada, `.mht` sem parte HTML e byte inválido.
    """
    extensao = caminho.suffix.lower()
    if extensao not in _EXTENSOES_MHT | _EXTENSOES_HTM:
        raise ErroFonte(f"extensão não suportada pelo leitor HTML: {caminho}")
    try:
        dados = caminho.read_bytes()
    except FileNotFoundError:
        raise ErroFonte(f"arquivo não encontrado: {caminho}") from None
    if extensao in _EXTENSOES_MHT:
        mensagem = email.message_from_bytes(dados, policy=email.policy.default)
        parte = _parte_html(mensagem, caminho)
        conteudo = parte.get_payload(decode=True)
        charset_mime = parte.get_content_charset()
        fonte = mensagem.get("Snapshot-Content-Location") or str(caminho)
        data = mensagem.get("Date")
    else:
        conteudo, charset_mime, fonte, data = dados, None, str(caminho), None
    charset = _charset(conteudo, charset_mime, caminho)
    return FonteLida(
        linhas=_linhas_logicas(conteudo, charset, relatorio),
        tipo_fonte="html",
        fonte=fonte,
        capturado_em=_capturado_em(data, caminho),
        sha256=hashlib.sha256(conteudo).hexdigest(),
    )


def _parte_html(mensagem: EmailMessage, caminho: Path) -> EmailMessage:
    for parte in mensagem.walk():
        if parte.get_content_type() == "text/html":
            return parte
    raise ErroFonte(f".mht sem parte text/html: {caminho}")


def _charset(conteudo: bytes, charset_mime: str | None, caminho: Path) -> str:
    """Charset do MIME, senão do `<meta>`, senão windows-1252 (H1), já validado no modo estrito.

    Byte inválido é `ErroFonte`, nunca `replace` (RNF04).
    """
    meta = _META_CHARSET.search(conteudo)
    charset = charset_mime or (meta[1].decode("ascii") if meta else _CHARSET_PADRAO)
    try:
        conteudo.decode(charset)
    except UnicodeDecodeError as erro:
        raise ErroFonte(
            f"byte inválido para {charset} na posição {erro.start}: {caminho}"
        ) from None
    except LookupError:
        raise ErroFonte(f"charset desconhecido {charset!r}: {caminho}") from None
    return charset


def _capturado_em(data: DateHeader | None, caminho: Path) -> str:
    """Cabeçalho `Date` do `.mht`; sem ele (e sempre no `.htm`), o `mtime` do arquivo. Em UTC."""
    instante = data.datetime if data else datetime.fromtimestamp(caminho.stat().st_mtime, tz=UTC)
    return instante.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class _Pedaco:
    """Nó de texto com o contexto de formatação de onde ele está no documento."""

    texto: str
    negrito: bool
    centralizado: bool
    tachado: bool


def _pedaco(no: NavigableString) -> _Pedaco:
    ancestrais = [pai for pai in no.parents if isinstance(pai, Tag)]
    # Como o CSS herda: decide o ancestral mais próximo que define o peso (H6).
    pesos = (_negrito_proprio(pai) for pai in ancestrais)
    return _Pedaco(
        texto=no,
        negrito=next((peso for peso in pesos if peso is not None), False),
        centralizado=any(pai.name in _BLOCOS and _bloco_centralizado(pai) for pai in ancestrais),
        tachado=any(_tachado_proprio(pai) for pai in ancestrais),
    )


def _negrito_proprio(tag: Tag) -> bool | None:
    """Peso que a própria tag define: `font-weight` no `style`, senão `<b>`/`<strong>`.

    `None` quando ela não define e o peso vem de fora. No CSS, número ≥ 600 é negrito.
    """
    peso = _FONT_WEIGHT.search(str(tag.get("style", "")))
    if peso:
        valor = peso[1].lower()
        return valor in _PESOS_NEGRITO or (valor.isdigit() and int(valor) >= 600)
    return True if tag.name in _NEGRITO else None


def _tachado_proprio(tag: Tag) -> bool:
    """H8: `<strike>`, `<s>`, `<del>` ou `line-through` no `style` da própria tag."""
    return tag.name in _TACHADO or bool(_LINE_THROUGH.search(str(tag.get("style", ""))))


def _bloco_centralizado(bloco: Tag) -> bool:
    """H5: `align="center"` em qualquer caixa, `text-align: center` no `style` ou `<center>`."""
    alinhamento = str(bloco.get("align", "")).lower()
    return (
        bloco.name == "center"
        or alinhamento == "center"
        or bool(_TEXT_ALIGN_CENTRO.search(str(bloco.get("style", ""))))
    )


def _colar(partes: list[_Pedaco]) -> str:
    return _ESPACO.sub(" ", "".join(p.texto for p in partes)).strip()


def _linhas_logicas(conteudo: bytes, charset: str, relatorio: Relatorio) -> tuple[LinhaFonte, ...]:
    """Uma linha por bloco ou `<br>` (H3, H4), com os nós de texto colados sem separador.

    Colar sem separador mantém `4<sup>o</sup>` como `4o` (H11). O parser é o do HTML5, o mesmo
    do navegador que salva o `.mht`: o Planalto fecha tags fora de ordem
    (`<b><i><p></i>Tempo do crime</b></p>`), e só a regra do HTML5 reabre o `<b>` dentro do
    `<p>`. Ela também lê `&#150;` pelo windows-1252 (`–`) e não para no `</html>` solto do CC.
    O parser recebe bytes e o charset, nunca `str`, para o `<meta charset>` não trocar a
    codificação no meio do documento.

    A `origem` conta também as linhas que saem pelo tachado (H8), para o descarte apontar o
    lugar exato; a saída pode ter lacunas na numeração.
    """
    linhas: list[LinhaFonte] = []
    partes: list[_Pedaco] = []
    posicao = 0

    def quebrar() -> None:
        nonlocal posicao
        linha = _colar(partes)
        # Só o caractere visível decide a flag: o `<b>` com espaço não marca a linha (H6).
        visiveis = [p for p in partes if p.texto.strip()]
        partes.clear()
        if not linha:
            return
        posicao += 1
        origem = f"html:p#{posicao}"
        tachado = _colar([p for p in visiveis if p.tachado])
        if tachado:  # H8; tachado só com espaço (os 6 do CP) não muda nada
            resto = _colar([p for p in visiveis if not p.tachado])
            if _SO_NOTAS.fullmatch(resto):
                # A linha sai com a nota: sozinha, o parser a colaria no dispositivo anterior.
                # `vazio`: fora do tachado não sobra texto; as notas seguem em `texto` (RF16).
                relatorio.registrar(
                    EntradaRelatorio(tipo="descarte", origem=origem, texto=linha, motivo="vazio")
                )
                return
            # Apagar o trecho adulteraria a frase vigente (CPP, art. 336, parágrafo único).
            relatorio.registrar(EntradaRelatorio(tipo="aviso", origem=origem, texto=tachado))
        negrito = all(p.negrito for p in visiveis)
        linhas.append(
            LinhaFonte(
                texto=linha,
                negrito=negrito,
                rotulo_negrito=visiveis[0].negrito and not negrito,
                centralizado=any(p.centralizado for p in visiveis),
                cor=None,
                origem=origem,
            )
        )

    pilha: list[object] = [BeautifulSoup(conteudo, "html5lib", from_encoding=charset)]
    while pilha:
        item = pilha.pop()
        if item is _FIM_DE_BLOCO:
            quebrar()
        elif isinstance(item, Tag):
            if item.name in _FORA_DO_TEXTO:
                continue
            if item.name == "br":
                quebrar()
                continue
            if item.name in _BLOCOS:
                quebrar()
                pilha.append(_FIM_DE_BLOCO)
            pilha.extend(reversed(item.contents))
        elif type(item) is NavigableString:  # comentário e doctype não são texto da norma
            partes.append(_pedaco(item))
    quebrar()
    return tuple(linhas)
