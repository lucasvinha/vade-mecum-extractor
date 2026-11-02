"""Conferência do texto legal do vade mecum em HTML contra os recortes (ver negocio/vade-mecum).

Etapa pura: recebe os recortes e o HTML já lidos, sem I/O. A LLM gera o HTML da Etapa 3, e esta
conferência garante que o texto legal dele é o dos recortes (ADR-005). Anotações não são
conferidas: só o que está nos campos `data-campo` dos nós `data-id`.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from vademecum.modelo import Base, No

CAMPOS = ("rotulo", "rubrica", "texto")
_SEM_NORMA = "-"  # `data-id` fora de qualquer `[data-norma]`


@dataclass(frozen=True, slots=True)
class Divergencia:
    """Uma linha do `conferir`: `<norma>:<id>: <motivo>`."""

    norma: str
    id: str
    motivo: str

    def __str__(self) -> str:
        return f"{self.norma}:{self.id}: {self.motivo}"


def _nos(nos: Sequence[No]) -> Iterator[No]:
    """Os nós da árvore na ordem do texto: o pai antes dos filhos."""
    for no in nos:
        yield no
        yield from _nos(no.filhos)


def _colapsar(texto: str) -> str:
    return " ".join(texto.split())  # `str.split()` também quebra no `\xa0` do `&nbsp;`


def _texto_do_campo(campo: Tag) -> str:
    """Texto do campo, sem o de nós `data-id` aninhados nele, que são conferidos à parte."""
    dono = campo.find_parent(attrs={"data-id": True})
    pedacos = [
        str(texto)
        for texto in campo.find_all(string=True)
        if isinstance(texto, NavigableString)
        and not isinstance(texto, Comment)
        and texto.find_parent(attrs={"data-id": True}) is dono
    ]
    return _colapsar("".join(pedacos))


def _campos(elemento: Tag) -> dict[str, list[str]]:
    """Os campos do nó: só conta o campo cujo `[data-id]` mais próximo é o próprio nó."""
    campos: dict[str, list[str]] = {}
    for campo in elemento.find_all(attrs={"data-campo": True}):
        if campo.find_parent(attrs={"data-id": True}) is elemento:
            campos.setdefault(campo["data-campo"], []).append(_texto_do_campo(campo))
    return campos


def _conferir_no(norma: str, no: No, elemento: Tag) -> Iterator[Divergencia]:
    campos = _campos(elemento)
    for nome in CAMPOS:
        esperado = getattr(no, nome, None) or ""
        achados = campos.pop(nome, [])
        if len(achados) > 1:
            yield Divergencia(norma, no.id, f"campo {nome} repetido")
        elif not achados:
            if esperado:
                yield Divergencia(norma, no.id, f"campo {nome} ausente")
        elif not esperado:
            yield Divergencia(norma, no.id, f"campo {nome} a mais")
        elif achados[0] != _colapsar(esperado):
            motivo = (
                f"campo {nome} divergente: esperado {_colapsar(esperado)!r}, no HTML {achados[0]!r}"
            )
            yield Divergencia(norma, no.id, motivo)
    for nome in sorted(campos):
        yield Divergencia(norma, no.id, f"campo {nome} desconhecido")


def conferir(recortes: Sequence[Base], html: str) -> tuple[Divergencia, ...]:
    """As divergências entre o texto legal do `html` e os `recortes`, uma por problema.

    Primeiro as do HTML, na ordem do documento (`data-id` desconhecido ou repetido); depois as dos
    recortes, na ordem da árvore (nó ausente, campo divergente). Sem divergência, tupla vazia.
    """
    esperados = {
        (recorte.norma.id, no.id): no for recorte in recortes for no in _nos(recorte.artigos)
    }
    documento = BeautifulSoup(html, "html5lib")
    achados: dict[tuple[str, str], Tag] = {}
    divergencias: list[Divergencia] = []
    for elemento in documento.find_all(attrs={"data-id": True}):
        dono = elemento.find_parent(attrs={"data-norma": True})
        chave = (dono["data-norma"] if dono is not None else _SEM_NORMA, elemento["data-id"])
        if chave not in esperados:
            divergencias.append(Divergencia(*chave, "data-id desconhecido"))
        elif chave in achados:
            divergencias.append(Divergencia(*chave, "data-id repetido"))
        else:
            achados[chave] = elemento
    for (norma, id_), no in esperados.items():
        elemento = achados.get((norma, id_))
        if elemento is None:
            divergencias.append(Divergencia(norma, id_, "nó ausente"))
        else:
            divergencias.extend(_conferir_no(norma, no, elemento))
    return tuple(divergencias)
