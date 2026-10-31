"""Modelo de dados da base e chave de ordenação dos dispositivos.

Sem dependência interna: toda etapa do pipeline importa daqui. O esquema está em
negocio/modelo-de-dados e a ordenação em negocio/recorte-e-cli.
"""

import re
from dataclasses import dataclass, field

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
