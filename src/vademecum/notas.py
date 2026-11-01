"""Notas legislativas: separa do texto e classifica (RF12; ver negocio/vigencia-e-notas).

Etapa pura. O vocabulário de cada tipo vem do perfil (ADR-002, P10); o resto das regras vale para
toda norma. O texto que sobra é literal: só sai a nota e o espaço antes dela.
"""

import re
from datetime import date

from vademecum.modelo import EntradaRelatorio, Nota, Relatorio
from vademecum.perfil import Perfil

# Tipo da nota sem gatilho do perfil que ainda cita norma (vai ao relatório; V6).
_OUTRA = "outra"
_CITA_NORMA = re.compile(r"\bLei n[º°o]|\bProvimento\b")
_PARENTESE = re.compile(r"\s*\([^()]*\)")
# H10: `Vigência` sem parênteses só no fim da linha (`… de 2022) Vigência`); com `v` minúsculo é
# texto (`durante sua vigência.`).
_TIPO_SEM_PARENTESES = "vigencia"
# Sobra de pontuação depois de tirar a nota (`Art. 359-Q. (VETADO).`): não é texto legal.
_SO_PONTUACAO = re.compile(r"[\s.;,:”“\"]*")
_ESPACO = re.compile(r"\s+")
_PONTUADO = (".", ";", ":", ",")

# Tipos de norma citados nas notas do Planalto. `Lei 12.550. de 2011` (CP, sem `nº` e com ponto)
# e `ADPF 1207 MC/DF` são casos reais; o número para antes do ponto que não vem seguido de dígito.
_NORMA = re.compile(
    r"(?:Lei Complementar|Decreto-Lei|Decreto|Lei|Medida [Pp]rovisória|Emenda Constitucional"
    r"|ADPF|ADI|ADC|Provimento(?: CG)?|Resolução(?: CNJ)?)"
    r"\s+(?:n[º°o]\.?\s*|Nº\s*)?\d+(?:\.\d+)*(?:-\d+)?"
)
# Ano: o número de 4 dígitos no fim, depois de `de` ou da vírgula (`de 11.7.1984`, `de 2025`,
# `, 1976`, `de 15 de 2001`); o número da `ADPF 1107` não é ano.
_ANO = re.compile(r"(?:\bde\s+|,\s*)(?:\d{1,2}º?\.\d{1,2}\.)?(?P<ano>\d{4})\)?$")
_DATA_PONTOS = re.compile(r"\bde\s+(?P<dia>\d{1,2})º?\.(?P<mes>\d{1,2})\.(?P<ano>\d{4})\)?$")
_MESES = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]
_DATA_EXTENSO = re.compile(
    rf"\bde\s+(?P<dia>\d{{1,2}})º?\s+de\s+(?P<mes>{'|'.join(_MESES)})\s+de\s+(?P<ano>\d{{4}})\)?$"
)


def extrair_notas(
    texto: str, perfil: Perfil, origem: str, relatorio: Relatorio
) -> tuple[str, tuple[Nota, ...]]:
    """`(texto_limpo, notas)`, com as notas na ordem do texto (RF12, H9, H10, P16).

    Parêntese que não começa por gatilho do perfil fica no texto (`(quatorze)`, `(art. 55)`),
    a não ser que cite norma (`Lei nº`, `Provimento`): aí vira nota `outra` e entra no relatório
    como `nota_outra`, para não sumir sem aviso (RNF04, V6).
    """
    notas: list[Nota] = []
    partes: list[str] = []
    fim = 0
    for casamento in _PARENTESE.finditer(texto):
        bruto = casamento[0].strip()
        tipo = _tipo(bruto[1:-1], perfil)
        if tipo is None:
            continue
        partes.append(texto[fim : casamento.start()])
        fim = casamento.end()
        # O ponto logo depois da nota que segue texto já pontuado é da nota, não do texto:
        # `ano. (Redação dada pela Lei nº 12.234, de 2010).` (CP, art. 109, VI) fica `ano.`.
        if texto.startswith(".", fim) and "".join(partes).rstrip().endswith(_PONTUADO):
            fim += 1
        notas.append(_nota(tipo, bruto))
        if tipo == _OUTRA:
            relatorio.registrar(EntradaRelatorio(tipo="nota_outra", origem=origem, texto=bruto))
    partes.append(texto[fim:])
    limpo = "".join(partes)
    for gatilho in dict(perfil.notas).get(_TIPO_SEM_PARENTESES, ()):
        sem = re.search(rf"(?:^|\s+){re.escape(gatilho)}\s*$", limpo)
        if sem:
            limpo = limpo[: sem.start()]
            notas.append(Nota(tipo=_TIPO_SEM_PARENTESES, bruto=gatilho))
            break
    limpo = _ESPACO.sub(" ", limpo).strip()
    if _SO_PONTUACAO.fullmatch(limpo):
        limpo = ""
    return limpo, tuple(notas)


def _tipo(conteudo: str, perfil: Perfil) -> str | None:
    for tipo, gatilhos in perfil.notas:
        if any(conteudo.startswith(gatilho) for gatilho in gatilhos):
            return tipo
    return _OUTRA if _CITA_NORMA.search(conteudo) else None


def _nota(tipo: str, bruto: str) -> Nota:
    norma = _NORMA.search(bruto)
    ano = _ANO.search(bruto)
    return Nota(
        tipo=tipo,
        bruto=bruto,
        norma=norma[0] if norma else None,
        ano=int(ano["ano"]) if ano else None,
        data=_data(bruto),
    )


def _data(bruto: str) -> str | None:
    """ISO `AAAA-MM-DD` só quando a nota traz dia, mês e ano (`de 11.7.1984`)."""
    pontos = _DATA_PONTOS.search(bruto)
    extenso = _DATA_EXTENSO.search(bruto)
    if pontos:
        dia, mes, ano = int(pontos["dia"]), int(pontos["mes"]), int(pontos["ano"])
    elif extenso:
        dia, mes, ano = int(extenso["dia"]), _MESES.index(extenso["mes"]) + 1, int(extenso["ano"])
    else:
        return None
    try:
        return date(ano, mes, dia).isoformat()
    except ValueError:  # data impossível na fonte: fica só o ano
        return None
