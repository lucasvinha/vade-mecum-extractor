"""Leitor do HTML do Planalto: `.mht` salvo pelo navegador → `FonteLida` (ver negocio/fontes).

Único lugar, com a `cli.py`, que lê arquivo (PADRAO_OURO). A unidade de saída é a linha lógica,
não o parágrafo HTML (H4).
"""

import email
import email.policy
import hashlib
import re
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from vademecum.modelo import ErroFonte, FonteLida, LinhaFonte, Relatorio

_EXTENSOES_MHT = frozenset({".mht", ".mhtml"})

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


def ler_html(caminho: Path, relatorio: Relatorio) -> FonteLida:
    """Lê a fonte HTML local e devolve as linhas lógicas na ordem do texto.

    `relatorio` recebe o texto da leitura que não vira linha (RNF04). Levanta `ErroFonte` para
    arquivo inexistente, extensão não suportada, `.mht` sem parte HTML e byte inválido.
    """
    if caminho.suffix.lower() not in _EXTENSOES_MHT:
        raise ErroFonte(f"extensão não suportada pelo leitor HTML: {caminho}")
    try:
        dados = caminho.read_bytes()
    except FileNotFoundError:
        raise ErroFonte(f"arquivo não encontrado: {caminho}") from None
    mensagem = email.message_from_bytes(dados, policy=email.policy.default)
    parte = _parte_html(mensagem, caminho)
    conteudo = parte.get_payload(decode=True)
    charset = _charset(conteudo, parte.get_content_charset(), caminho)
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
        fonte=mensagem.get("Snapshot-Content-Location") or str(caminho),
        capturado_em=_capturado_em(mensagem, caminho),
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


def _capturado_em(mensagem: EmailMessage, caminho: Path) -> str:
    """Cabeçalho `Date` do `.mht`; sem ele, o `mtime` do arquivo. Sempre em UTC."""
    data = mensagem.get("Date")
    instante = data.datetime if data else datetime.fromtimestamp(caminho.stat().st_mtime, tz=UTC)
    return instante.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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
