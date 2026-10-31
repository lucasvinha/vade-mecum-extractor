"""Leitor do HTML do Planalto: `.mht` do navegador ou `.htm` → `FonteLida` (ver negocio/fontes).

Único lugar, com a `cli.py`, que lê arquivo (PADRAO_OURO). A unidade de saída é a linha lógica,
não o parágrafo HTML (H4).
"""

import email
import email.policy
import hashlib
import re
from datetime import UTC, datetime
from email.headerregistry import DateHeader
from email.message import EmailMessage
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from vademecum.modelo import ErroFonte, FonteLida, LinhaFonte, Relatorio

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
_FIM_DE_BLOCO = object()
_ESPACO = re.compile(r"\s+")  # em `str`, `\s` inclui o `\xa0` do `&nbsp;`

# O libxml2 lê `&#150;` como o controle U+0096; o navegador, pela regra do HTML5, lê o byte em
# windows-1252 (`–`). É o que o `.mht` traz, e o `.htm` tem de dar as mesmas linhas.
_REFERENCIA_C1 = re.compile(rb"&#(1[2-5]\d);")
# O libxml2 descarta o que vem depois de `</html>`, e o CC tem um logo após o preâmbulo (RNF04).
# Os dois fechos não têm texto: tirá-los não perde nada.
_FECHO_DE_DOCUMENTO = re.compile(rb"</(?:body|html)\s*>", re.IGNORECASE)


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
    linhas = tuple(
        LinhaFonte(
            texto=t,
            negrito=False,
            rotulo_negrito=False,
            centralizado=False,
            cor=None,
            origem=f"html:p#{n}",
        )
        for n, t in enumerate(_linhas_logicas(conteudo, charset), start=1)
    )
    return FonteLida(
        linhas=linhas,
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


def _referencia_windows_1252(referencia: re.Match[bytes]) -> bytes:
    """`&#150;` → `&#8211;`. Os 5 bytes sem caractere no windows-1252 ficam como estão (HTML5)."""
    try:
        caractere = bytes([int(referencia[1])]).decode("windows-1252")
    except UnicodeDecodeError:
        return referencia[0]
    return b"&#%d;" % ord(caractere)


def _linhas_logicas(conteudo: bytes, charset: str) -> list[str]:
    """Uma linha por bloco ou `<br>` (H3, H4), com os nós de texto colados sem separador.

    Colar sem separador mantém `4<sup>o</sup>` como `4o` (H11). O lxml recebe bytes e o charset,
    nunca `str`: com `str`, o `<meta charset>` o faz trocar de codificação no meio do documento
    (mojibake e texto truncado no CP inteiro a partir do art. 266).
    """
    linhas: list[str] = []
    partes: list[str] = []

    def quebrar() -> None:
        linha = _ESPACO.sub(" ", "".join(partes)).strip()
        partes.clear()
        if linha:
            linhas.append(linha)

    conteudo = _REFERENCIA_C1.sub(_referencia_windows_1252, _FECHO_DE_DOCUMENTO.sub(b"", conteudo))
    pilha: list[object] = [BeautifulSoup(conteudo, "lxml", from_encoding=charset)]
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
            partes.append(item)
    quebrar()
    return linhas
