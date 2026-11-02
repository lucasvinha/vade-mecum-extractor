"""Recorte de uma base pela expressão de artigos do edital (RF18; ver negocio/recorte-e-cli).

Etapa pura: recebe a expressão e a base já lidas, sem I/O. A semântica da faixa é a do ADR-004.
"""

import re
from dataclasses import dataclass

from vademecum.modelo import ErroFonte, chave_de_texto

# Edital: `8º; 9º; 18`, `12, 13`.
_SEPARADOR_ITEM = re.compile(r"[;,]")
# Edital: `1º a 12`, `994–1.091`, `293-305`. Depois de `-`, só dígito fecha a faixa: letra é
# sufixo (`359-M-A`, `121-A–130`), e o hífen sem dígito depois fica no número e o torna ilegível.
_SEPARADOR_FAIXA = re.compile(r"\s*–\s*|\s+a\s+|\s*-\s*(?=\d)")

Chave = tuple[int, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class Item:
    """Item da expressão: avulso tem `inicio == fim` (P1); `qualificadores` são ignorados (P2)."""

    texto: str  # como foi escrito, sem espaço nas pontas
    inicio: Chave
    fim: Chave
    qualificadores: tuple[str, ...] = ()


def _chave(ponta: str, item: str) -> Chave:
    try:
        return chave_de_texto(ponta)
    except ValueError:
        raise ErroFonte(f"item ilegível na expressão de artigos: {item!r}") from None


def _item(texto: str) -> Item:
    pontas = _SEPARADOR_FAIXA.split(texto)
    if len(pontas) > 2:
        raise ErroFonte(f"item ilegível na expressão de artigos: {texto!r}")
    inicio = _chave(pontas[0], texto)
    fim = _chave(pontas[-1], texto)
    if fim < inicio:
        raise ErroFonte(f"faixa invertida na expressão de artigos: {texto!r}")
    return Item(texto=texto, inicio=inicio, fim=fim)


def interpretar(expressao: str) -> tuple[Item, ...]:
    """Itens da expressão, na ordem escrita; `ErroFonte` citando o item que não se lê."""
    itens: list[Item] = []
    for pedaco in _SEPARADOR_ITEM.split(expressao):
        texto = pedaco.strip()
        if not texto:
            raise ErroFonte(f"item vazio na expressão de artigos: {expressao!r}")
        if texto[0].isdigit():
            itens.append(_item(texto))
        elif itens:
            # P2: `196, inciso XX` recorta o artigo inteiro; o trecho vira aviso no recorte.
            anterior = itens[-1]
            itens[-1] = Item(
                anterior.texto, anterior.inicio, anterior.fim, (*anterior.qualificadores, texto)
            )
        else:
            raise ErroFonte(f"qualificador sem artigo antes na expressão de artigos: {texto!r}")
    return tuple(itens)
