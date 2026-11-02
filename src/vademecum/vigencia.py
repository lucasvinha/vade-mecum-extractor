"""Vigência: tira da árvore o que caiu e registra o descarte (ADR-001, negocio/vigencia-e-notas).

Etapa pura. O nó sai quando o texto sem notas é vazio ou só `Revogado.`, com um gatilho de
`notas.revogacao` do perfil (P12), e todos os filhos também saem (RF14). Nó vazio com filho
vigente fica, para a V5 acusar: não se descarta texto vigente. A pena nunca sai. A rubrica sai com
o nó (H16), e ids e penas restantes não são renumerados. O nome de nível só existe no `local` dos
artigos: o nível que fica sem artigo vigente vai ao relatório como `aviso` (RNF04).
"""

from dataclasses import fields, replace

from vademecum.modelo import EntradaRelatorio, Local, No, Relatorio
from vademecum.perfil import Perfil

_PENA = "pena"
_REVOGACAO = "revogacao"
_VETO = "veto"
# RF16: a primeira nota de veto ou revogação dá o motivo; sem nenhuma, o nó só estava vazio.
_MOTIVO_POR_NOTA = {_VETO: "vetado", _REVOGACAO: "revogado"}


def filtrar_vigentes(
    artigos: tuple[No, ...], perfil: Perfil, relatorio: Relatorio
) -> tuple[No, ...]:
    """Os artigos sem os nós descartados; um `descarte` por nó, em pré-ordem (RF14, RF16)."""
    revogado = tuple(f"{gatilho}." for gatilho in dict(perfil.notas).get(_REVOGACAO, ()))
    descartes: list[EntradaRelatorio] = []
    vigentes = []
    for artigo in artigos:
        vigente = _filtrar(artigo, revogado, descartes)
        if vigente is not None:
            vigentes.append(vigente)
    for descarte in descartes:
        relatorio.registrar(descarte)
    for aviso in _niveis_sem_vigente(artigos, vigentes):
        relatorio.registrar(aviso)
    return tuple(vigentes)


def _niveis(artigo: No) -> list[tuple[str | None, ...]]:
    """O caminho de cada nível do `local`, da raiz até ele.

    O caminho, e não só o nome, distingue o `CAPÍTULO I` que se repete em cada título.
    """
    if artigo.local is None:
        return []
    valores = tuple(getattr(artigo.local, campo.name) for campo in fields(Local))
    return [valores[: i + 1] for i, valor in enumerate(valores) if valor is not None]


def _niveis_sem_vigente(artigos: tuple[No, ...], vigentes: list[No]) -> list[EntradaRelatorio]:
    # RNF04: sem artigo vigente, o nome do nível sairia da base sem entrar no relatório
    # (CP, Título III, Caps. II a IV, arts. 187 a 196).
    # A `origem` é a do primeiro artigo descartado do nível.
    restantes = {caminho for artigo in vigentes for caminho in _niveis(artigo)}
    perdidos: dict[tuple[str | None, ...], str] = {}
    for artigo in artigos:
        for caminho in _niveis(artigo):
            if caminho not in restantes:
                perdidos.setdefault(caminho, artigo.origem)
    return [
        EntradaRelatorio(
            tipo="aviso", origem=origem, texto=f"RNF04: nível sem artigo vigente: {caminho[-1]}"
        )
        for caminho, origem in perdidos.items()
    ]


def _filtrar(no: No, revogado: tuple[str, ...], descartes: list[EntradaRelatorio]) -> No | None:
    """O nó com os filhos vigentes, ou `None` quando ele sai inteiro; acumula os descartes."""
    dos_filhos: list[EntradaRelatorio] = []
    filhos = []
    for filho in no.filhos:
        vigente = _filtrar(filho, revogado, dos_filhos)
        if vigente is not None:
            filhos.append(vigente)
    # H15: `Revogado o livramento…` (art. 88) é texto vigente; só o gatilho com ponto, sozinho.
    caiu = no.texto == "" or no.texto in revogado
    if no.tipo != _PENA and caiu and not filhos:
        descartes.append(_descarte(no, revogado))
        descartes.extend(dos_filhos)
        return None
    if not dos_filhos:  # nada saiu da subárvore: o nó volta como veio
        return no
    descartes.extend(dos_filhos)
    return replace(no, filhos=tuple(filhos))


def _descarte(no: No, revogado: tuple[str, ...]) -> EntradaRelatorio:
    motivo = next((_MOTIVO_POR_NOTA[n.tipo] for n in no.notas if n.tipo in _MOTIVO_POR_NOTA), None)
    if motivo is None:
        motivo = "revogado" if no.texto in revogado else "vazio"
    partes = (no.rotulo, no.texto, *(nota.bruto for nota in no.notas))
    return EntradaRelatorio(
        tipo="descarte",
        origem=no.origem,
        texto=" ".join(parte for parte in partes if parte),
        id=no.id,
        rotulo=no.rotulo,
        rubrica=no.rubrica,
        motivo=motivo,
        notas=no.notas,
    )
