"""Normalizador: ordinal e travessão do rótulo no início da linha (H11, H13).

Etapa pura, sem perfil e sem relatório: os prefixos de artigo chegam por parâmetro (ADR-002).
Só o rótulo muda; o corpo é texto legal e fica literal (`dos §§ 4o e 6o do art. 121`).
A junção de linhas e a separação de notas não são daqui (ver negocio/pipeline-e-perfis).
"""

import re
from collections.abc import Iterable
from dataclasses import replace

from vademecum.modelo import LinhaFonte

# H11: o ordinal só conta colado ao número (`4o`, `2°`, `2o-A`) e antes de algo que não é letra,
# para `Art. 10 -` e `Art. 121.` não mudarem. Milhar opcional (`1.091`, P13).
_NUMERO = r"(?:\d{1,3}(?:\.\d{3})+|\d+)"
_ORDINAL = r"(?P<ordinal>[º°o](?!\w))?"
_SUFIXO = r"(?P<sufixo>(?:-[A-Z])*\.?)"

# H13: o separador `–` só vira `-` logo depois de um destes rótulos ou de um rótulo numerado.
_ROTULO_SEM_NUMERO = r"(?P<rotulo>Parágrafo único\.?|[IVXLCDM]+(?!\w)|Pena)"
_SEPARADOR = r"(?P<separador>\s*–)?"


def _padrao(prefixos_artigo: Iterable[str]) -> re.Pattern[str]:
    # O mais longo primeiro: `Artigo` antes de `Art`, para não parar no meio da palavra (P9).
    prefixos = [re.escape(p) for p in sorted(prefixos_artigo, key=len, reverse=True)]
    numerado = rf"(?P<numerado>(?:{'|'.join([*prefixos, '§'])})\s*{_NUMERO})"
    return re.compile(rf"^(?:{numerado}{_ORDINAL}{_SUFIXO}|{_ROTULO_SEM_NUMERO}){_SEPARADOR}")


def normalizar(
    linhas: Iterable[LinhaFonte], prefixos_artigo: Iterable[str]
) -> tuple[LinhaFonte, ...]:
    """Troca `o`/`°` por `º` no ordinal e `–` por `-` no separador do rótulo inicial (H11, H13)."""
    padrao = _padrao(prefixos_artigo)
    return tuple(_normalizar_linha(linha, padrao) for linha in linhas)


def _normalizar_linha(linha: LinhaFonte, padrao: re.Pattern[str]) -> LinhaFonte:
    casamento = padrao.match(linha.texto)
    if casamento is None:
        return linha
    if casamento["numerado"] is not None:
        ordinal = "º" if casamento["ordinal"] else ""
        rotulo = casamento["numerado"] + ordinal + casamento["sufixo"]
    else:
        rotulo = casamento["rotulo"]
    separador = (casamento["separador"] or "").replace("–", "-")
    novo = rotulo + separador + linha.texto[casamento.end() :]
    return linha if novo == linha.texto else replace(linha, texto=novo)
