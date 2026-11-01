"""Validador: confere a base pronta contra V1–V6 e só registra `aviso` (ver PADRAO_OURO).

Etapa pura, que não muda a base. Cada aviso começa pelo ID da regra (`V2: …`) e leva a `origem`
do nó mais próximo. A V7 (linha não classificada) é do parser, que já registra `nao_classificada`.
"""

from collections import Counter
from collections.abc import Iterator
from itertools import pairwise

from vademecum.modelo import Base, EntradaRelatorio, No, Relatorio, chave_de_texto, chave_ordenacao
from vademecum.perfil import Perfil

_PENA = "pena"
_OUTRA = "outra"


def validar(base: Base, perfil: Perfil, relatorio: Relatorio) -> None:
    """Registra no `relatorio` um `aviso` por violação de V1 a V6; não levanta erro."""
    avisos: list[EntradaRelatorio] = []
    _v1_ordem(base.artigos, avisos)
    if perfil.lacunas:
        _v2_lacunas(base.artigos, relatorio, avisos)
    _v3_ids(base.artigos, avisos)
    for artigo in base.artigos:
        for no in _pre_ordem(artigo):
            _v4_irmaos(no, avisos)
    _v5_vazios(base.artigos, avisos)
    _v6_notas_outra(base.artigos, relatorio, avisos)
    for aviso in avisos:
        relatorio.registrar(aviso)


def _aviso(regra: str, no: No, texto: str) -> EntradaRelatorio:
    return EntradaRelatorio(tipo="aviso", origem=no.origem, texto=f"{regra}: {texto}")


def _pre_ordem(no: No) -> Iterator[No]:
    yield no
    for filho in no.filhos:
        yield from _pre_ordem(filho)


def _todos(artigos: tuple[No, ...]) -> Iterator[No]:
    for artigo in artigos:
        yield from _pre_ordem(artigo)


def _chave(artigo: No) -> tuple[int, tuple[str, ...]]:
    return chave_ordenacao(artigo.numero or 0, artigo.sufixo)


def _v1_ordem(artigos: tuple[No, ...], avisos: list[EntradaRelatorio]) -> None:
    for anterior, artigo in pairwise(artigos):
        if _chave(artigo) <= _chave(anterior):
            avisos.append(
                _aviso("V1", artigo, f"{artigo.id} fora de ordem, depois de {anterior.id}")
            )


def _v2_lacunas(
    artigos: tuple[No, ...], relatorio: Relatorio, avisos: list[EntradaRelatorio]
) -> None:
    # H19, ADR-003: o artigo revogado sai da base (ADR-001), mas conta pelo descarte de artigo.
    descartados = {
        chave_de_texto(e.id.removeprefix("art"))[0]
        for e in relatorio.entradas
        if e.tipo == "descarte" and e.id is not None and "." not in e.id
    }
    presentes = {artigo.numero for artigo in artigos if artigo.numero is not None} | descartados
    if not presentes or not artigos:
        return
    seguinte = {}  # número que falta → artigo da base logo depois dele, para a `origem`
    for numero in range(max(presentes), 0, -1):
        if numero in presentes:
            continue
        seguinte[numero] = next((a for a in artigos if (a.numero or 0) > numero), artigos[-1])
    for numero in sorted(seguinte):
        avisos.append(_aviso("V2", seguinte[numero], f"lacuna na numeração-base: art. {numero}"))


def _v3_ids(artigos: tuple[No, ...], avisos: list[EntradaRelatorio]) -> None:
    contagem = Counter(no.id for no in _todos(artigos))
    vistos: set[str] = set()
    for no in _todos(artigos):
        if contagem[no.id] > 1 and no.id not in vistos:
            vistos.add(no.id)
            avisos.append(_aviso("V3", no, f"id duplicado: {no.id} ({contagem[no.id]} vezes)"))


def _chave_irmao(no: No) -> tuple[int, tuple[str, ...]] | None:
    """Chave do rótulo pelo último segmento do id (`p2-A`, `i7`, `a`); `None` fora da V4."""
    segmento = no.id.rsplit(".", 1)[-1]
    if no.tipo == "paragrafo" and segmento != "pu":
        return chave_de_texto(segmento.removeprefix("p"))
    if no.tipo == "inciso":
        return chave_ordenacao(int(segmento.removeprefix("i")), ())
    if no.tipo == "alinea":
        return chave_ordenacao(ord(segmento), ())
    return None


def _v4_irmaos(pai: No, avisos: list[EntradaRelatorio]) -> None:
    maior: dict[str, tuple[No, tuple[int, tuple[str, ...]]]] = {}
    for filho in pai.filhos:
        chave = _chave_irmao(filho)
        if chave is None:
            continue
        anterior = maior.get(filho.tipo)
        if anterior is not None and chave < anterior[1]:
            avisos.append(
                _aviso("V4", filho, f"{filho.id} fora de ordem, depois de {anterior[0].id}")
            )
        else:
            maior[filho.tipo] = (filho, chave)


def _v5_vazios(artigos: tuple[No, ...], avisos: list[EntradaRelatorio]) -> None:
    # ADR-001: o nó vazio com filho vigente fica na base, e é aqui que ele aparece.
    for no in _todos(artigos):
        if no.tipo != _PENA and no.texto == "":
            avisos.append(_aviso("V5", no, f"texto vazio em dispositivo vigente: {no.id}"))


def _v6_notas_outra(
    artigos: tuple[No, ...], relatorio: Relatorio, avisos: list[EntradaRelatorio]
) -> None:
    registradas = {e.texto for e in relatorio.entradas if e.tipo == "nota_outra"}
    for no in _todos(artigos):
        for nota in no.notas:
            if nota.tipo == _OUTRA and nota.bruto not in registradas:
                avisos.append(
                    _aviso("V6", no, f"nota outra sem registro no relatório: {nota.bruto}")
                )
