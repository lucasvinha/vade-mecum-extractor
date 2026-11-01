"""Vigência: tira da árvore o que caiu e registra o descarte (ADR-001, negocio/vigencia-e-notas).

Etapa pura. O nó sai quando o texto sem notas é vazio ou só `Revogado.`, com um gatilho de
`notas.revogacao` do perfil (P12), e todos os filhos também saem (RF14). Nó vazio com filho
vigente fica, para a V5 acusar: não se descarta texto vigente. A pena nunca sai. A rubrica sai com
o nó (H16), e ids e penas restantes não são renumerados.
"""

from dataclasses import replace

from vademecum.modelo import EntradaRelatorio, No, Relatorio
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
    return tuple(vigentes)


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
