"""Modelo de dados da base, chave de ordenação dos dispositivos e serialização (RNF03).

Sem dependência interna: toda etapa do pipeline importa daqui. O esquema está em
negocio/modelo-de-dados e a ordenação em negocio/recorte-e-cli.
"""

import json
import re
from dataclasses import dataclass, field, fields, is_dataclass

from vademecum import SCHEMA_VERSION

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


# Romano canônico do inciso (`I` a `LXXVIII` na CF); forma não canônica (`IIII`, `VX`) é erro.
_ROMANO = re.compile(r"(?=[MDCLXVI])M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})")
_VALOR_ROMANO = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _numero_com_sufixo(numero: int, sufixo: tuple[str, ...]) -> str:
    return "-".join((str(numero), *sufixo))


def id_artigo(numero: int, sufixo: tuple[str, ...] = ()) -> str:
    """`art121`, `art359-M-A`; o número já vem sem separador de milhar (`art1091-A`, P13)."""
    return f"art{_numero_com_sufixo(numero, sufixo)}"


def id_paragrafo(pai: str, numero: int | None, sufixo: tuple[str, ...] = ()) -> str:
    """`<pai>.p2`, `<pai>.p2-B`; `numero` é `None` no parágrafo único (`<pai>.pu`)."""
    if numero is None:
        return f"{pai}.pu"
    return f"{pai}.p{_numero_com_sufixo(numero, sufixo)}"


def id_inciso(pai: str, romano: str) -> str:
    """`<pai>.i7` para o inciso `VII`: o romano vira inteiro."""
    if _ROMANO.fullmatch(romano) is None:
        raise ValueError(f"inciso romano inválido: {romano!r}")
    valores = [_VALOR_ROMANO[c] for c in romano]
    # Algarismo menor antes de um maior subtrai (`IV`, `XL`).
    numero = sum(-v if v < prox else v for v, prox in zip(valores, [*valores[1:], 0], strict=True))
    return f"{pai}.i{numero}"


def id_alinea(pai: str, letra: str) -> str:
    """`<pai>.a`."""
    return f"{pai}.{letra}"


def id_pena(pai: str, ordem: int) -> str:
    """`<pai>.pena1`; `ordem` conta só as penas do mesmo pai, a partir de 1."""
    if ordem < 1:
        raise ValueError(f"ordem da pena começa em 1: {ordem}")
    return f"{pai}.pena{ordem}"


class ErroFonte(Exception):
    """Erro de entrada (arquivo inexistente, PDF sem texto; RF06); a CLI devolve código 2."""


@dataclass(frozen=True, slots=True)
class LinhaFonte:
    """Linha lida da fonte; o contrato central do pipeline (ver negocio/pipeline-e-perfis)."""

    texto: str  # já com espaços colapsados
    negrito: bool  # linha inteiramente em negrito
    rotulo_negrito: bool  # só o início da linha em negrito (padrão do PDF)
    centralizado: bool
    cor: str | None  # útil para notas e títulos no PDF
    origem: str  # "html:p#123" | "pdf:p3:col2:l14" (rastreabilidade)


@dataclass(frozen=True, slots=True)
class Nota:
    """Nota legislativa de um nó (ver negocio/vigencia-e-notas)."""

    tipo: str
    bruto: str  # texto original da nota
    norma: str | None = None
    ano: int | None = None
    data: str | None = None  # ISO `AAAA-MM-DD`; `None` quando a fonte só traz o ano


@dataclass(frozen=True, slots=True)
class Local:
    """Posição do artigo na hierarquia da norma; nível ausente fica `None` (P8)."""

    parte: str | None = None
    livro: str | None = None
    titulo: str | None = None
    capitulo: str | None = None
    secao: str | None = None
    subsecao: str | None = None
    rotulo_livre: str | None = None


@dataclass(frozen=True, slots=True)
class No:
    """Nó da árvore de dispositivos; as chaves emitidas por `tipo` estão em negocio/modelo-de-dados.

    `filhos` preserva a ordem do texto, com penas e dispositivos intercalados (H14). `origem`
    fica só na memória, para depurar o parser (RF19); não entra no JSON.
    """

    id: str
    tipo: str
    texto: str
    origem: str
    rotulo: str | None = None
    numero: int | None = None  # só no artigo, sem separador de milhar (P13)
    sufixo: tuple[str, ...] = ()  # só no artigo, letras na ordem do rótulo (H11, H12)
    rubrica: str | None = None
    local: Local | None = None  # só no artigo
    notas: tuple[Nota, ...] = ()
    parcial: bool = False  # só no artigo: a fonte o traz incompleto (P7)
    filhos: tuple["No", ...] = ()


@dataclass(frozen=True, slots=True)
class Norma:
    """Identificação da norma e da captura; `capturado_em` e `sha256` só aqui (RNF03)."""

    id: str
    titulo: str
    ementa: str | None
    tipo_fonte: str  # "html" | "pdf"
    fonte: str
    capturado_em: str
    sha256: str
    perfil: str


@dataclass(frozen=True, slots=True)
class Metadados:
    """O que fica fora da árvore de artigos (H17); único bloco que pode diferir na A14."""

    preambulo: str | None = None
    rodape: str | None = None


@dataclass(frozen=True, slots=True)
class Recorte:
    """Expressão que gerou o recorte e a base de onde ele saiu (ver negocio/recorte-e-cli)."""

    expressao: str
    origem: str


@dataclass(frozen=True, slots=True)
class Base:
    """Envelope da base ou do recorte; `recorte` é `None` na base completa."""

    norma: Norma
    metadados: Metadados
    artigos: tuple[No, ...] = ()
    recorte: Recorte | None = None


# RNF04: todo texto fora da árvore cai num destes tipos (ver docs/README.md, Contratos).
TIPOS_ENTRADA = frozenset({"descarte", "aviso", "nao_classificada", "nota_outra", "faixa_revogada"})


@dataclass(frozen=True, slots=True)
class EntradaRelatorio:
    """Texto que não entrou na árvore, com a `origem` de onde saiu (RNF04).

    Os campos próprios de cada tipo (motivo do descarte, faixa revogada) chegam com a etapa que
    gera a entrada.
    """

    tipo: str
    origem: str
    texto: str

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_ENTRADA:
            raise ValueError(f"tipo de entrada do relatório inválido: {self.tipo!r}")


@dataclass(slots=True)
class Relatorio:
    """Acumulador das entradas do relatório; `registrar` é o único método de escrita."""

    _entradas: list[EntradaRelatorio] = field(default_factory=list, init=False, repr=False)

    def registrar(self, entrada: EntradaRelatorio) -> None:
        self._entradas.append(entrada)

    @property
    def entradas(self) -> tuple[EntradaRelatorio, ...]:
        """Entradas na ordem em que foram registradas."""
        return tuple(self._entradas)


# Esquema estável por tipo (ver negocio/modelo-de-dados): chave de outro tipo não sai, e `origem`
# fica só na memória (RF19).
_CHAVES_DISPOSITIVO = ("id", "tipo", "rotulo", "rubrica", "texto", "notas", "filhos")
_CHAVES_POR_TIPO = {
    "artigo": (*_CHAVES_DISPOSITIVO, "numero", "sufixo", "local", "parcial"),
    **dict.fromkeys(("paragrafo", "inciso", "alinea", "item"), _CHAVES_DISPOSITIVO),
    "pena": ("id", "tipo", "texto", "notas"),
}


def _para_dict(valor):
    if isinstance(valor, No):
        chaves = _CHAVES_POR_TIPO.get(valor.tipo)
        if chaves is None:
            raise ValueError(f"tipo de nó sem esquema: {valor.tipo!r} em {valor.id!r}")
        return {chave: _para_dict(getattr(valor, chave)) for chave in chaves}
    if is_dataclass(valor):
        return {f.name: _para_dict(getattr(valor, f.name)) for f in fields(valor)}
    if isinstance(valor, tuple):
        return [_para_dict(item) for item in valor]
    return valor


def para_json(obj: Base | Relatorio) -> str:
    """Texto JSON determinístico da base ou do relatório (RNF03); quem grava é a `cli.py`."""
    if isinstance(obj, Relatorio):
        dados = {"entradas": _para_dict(obj.entradas)}
    else:
        dados = {"schema_version": SCHEMA_VERSION, **_para_dict(obj)}
    return json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
