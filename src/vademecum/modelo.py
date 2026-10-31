"""Modelo de dados da base e chave de ordenação dos dispositivos.

Sem dependência interna: toda etapa do pipeline importa daqui. O esquema está em
negocio/modelo-de-dados e a ordenação em negocio/recorte-e-cli.
"""

import re

# H11, H12, P13: milhar opcional (`1.091`), ordinal opcional (`1º`, `2°`, `4o`) e sufixos
# maiúsculos de um ou mais níveis (`121-A`, `359-M-A`). O prefixo `Art.` é do perfil (ADR-002).
_NUMERO_DISPOSITIVO = re.compile(
    r"(?P<numero>\d{1,3}(?:\.\d{3})+|\d+)[º°o]?(?P<sufixo>(?:-[A-Z])*)"
)


def chave_ordenacao(numero: int, sufixo: tuple[str, ...]) -> tuple[int, tuple[str, ...]]:
    """Chave `(numero, sufixo)`; a tupla vazia ordena antes de qualquer letra (H12)."""
    return (numero, sufixo)


def chave_de_texto(s: str) -> tuple[int, tuple[str, ...]]:
    """Chave de ordenação do fragmento numérico de um rótulo (`1º`, `1.091-A`, `359-M-A`).

    Levanta `ValueError` para qualquer outra forma, inclusive com prefixo (`Art. 121`) ou sufixo
    minúsculo (`121-a`).
    """
    casamento = _NUMERO_DISPOSITIVO.fullmatch(s)
    if casamento is None:
        raise ValueError(f"número de dispositivo inválido: {s!r}")
    numero = int(casamento["numero"].replace(".", ""))  # P13
    sufixo = tuple(casamento["sufixo"].split("-")[1:])
    return chave_ordenacao(numero, sufixo)
