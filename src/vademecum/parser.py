"""Parser: linhas normalizadas → árvore artigo › parágrafo › inciso › alínea (ver negocio/parsing).

Etapa pura, máquina de estados sobre as linhas. Os prefixos de artigo vêm do perfil (ADR-002, P9);
os regex partem da tabela de negocio/parsing e rodam depois do `normalizador`, com ordinal em `º`
e separador em `-`. As notas saem do texto por `notas.extrair_notas` (RF12).
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

from vademecum.modelo import (
    EntradaRelatorio,
    LinhaFonte,
    No,
    Nota,
    Relatorio,
    chave_de_texto,
    id_alinea,
    id_artigo,
    id_inciso,
    id_paragrafo,
    id_pena,
)
from vademecum.notas import extrair_notas
from vademecum.perfil import Perfil

# RF08, H11, H12, P13: o fragmento numérico vai inteiro para `chave_de_texto`.
_NUMERO = r"(?P<numero>(?:\d{1,3}(?:\.\d{3})+|\d+)º?(?:-[A-Z])*)"
_RESTO = r"\s*[-.]?\s*(?P<texto>.*)"
_PARAGRAFO = re.compile(rf"^(?P<rotulo>§\s*{_NUMERO}){_RESTO}$")
_PARAGRAFO_UNICO = re.compile(r"^(?P<rotulo>Parágrafo\s+único)\s*[-.:]?\s*(?P<texto>.*)$", re.I)
# RF08: romano + hífen, ou romano + espaço + minúscula (`III perda ou inutilização…`, CP, art. 129,
# § 2º, `p#684`, sem hífen na fonte). O romano não canônico (`MIL`) não é inciso.
_INCISO = re.compile(r"^(?P<romano>[IVXLCDM]+)(?:\s*-\s*|\s+(?=[a-zà-ÿ]))(?P<texto>.*)$")
_ALINEA = re.compile(r"^(?P<letra>[a-z])\)\s*(?P<texto>.*)$")
# RF09, H14: `Pena -` ou `Pena:` (CP, art. 319-A, `p#2032`); `Pena de multa` é rubrica.
_PENA = re.compile(r"^Pena\s*[-:]\s*(?P<texto>.*)$")


@dataclass(slots=True)
class _Em:
    """Nó em construção; vira `No` congelado no fim."""

    id: str
    tipo: str
    origem: str
    rotulo: str | None = None
    numero: int | None = None
    sufixo: tuple[str, ...] = ()
    textos: list[str] = field(default_factory=list)
    notas: list[Nota] = field(default_factory=list)
    filhos: list["_Em"] = field(default_factory=list)
    penas: int = 0

    def acrescentar(self, texto: str, notas: Iterable[Nota]) -> None:
        if texto:
            self.textos.append(texto)
        self.notas.extend(notas)

    def congelar(self) -> No:
        return No(
            id=self.id,
            tipo=self.tipo,
            texto=" ".join(self.textos),
            origem=self.origem,
            rotulo=self.rotulo,
            numero=self.numero,
            sufixo=self.sufixo,
            notas=tuple(self.notas),
            filhos=tuple(filho.congelar() for filho in self.filhos),
        )


@dataclass(slots=True)
class _Estado:
    """Ramo aberto da árvore: o artigo e, abaixo dele, o parágrafo, o inciso e a alínea."""

    artigos: list[_Em] = field(default_factory=list)
    paragrafo: _Em | None = None
    inciso: _Em | None = None
    alinea: _Em | None = None
    corrente: _Em | None = None  # quem recebe a continuação (RF11)

    @property
    def artigo(self) -> _Em | None:
        return self.artigos[-1] if self.artigos else None


def analisar(linhas: Iterable[LinhaFonte], perfil: Perfil, relatorio: Relatorio) -> tuple[No, ...]:
    """Artigos na ordem da fonte, com parágrafos, incisos, alíneas e penas (RF08, RF09, RF11).

    Linha sem dispositivo aberto que a receba vai ao relatório como `nao_classificada` (V7, RNF04).
    """
    artigo = _padrao_artigo(perfil.prefixos_artigo)
    estado = _Estado()
    for linha in linhas:
        if not linha.texto:
            continue
        if not _dispositivo(linha, artigo, perfil, estado, relatorio):
            _continuacao(linha, perfil, estado, relatorio)
    return tuple(em.congelar() for em in estado.artigos)


def _padrao_artigo(prefixos: Iterable[str]) -> re.Pattern[str]:
    # O mais longo primeiro, como no normalizador: `Artigo` antes de `Art` (P9).
    alternativas = "|".join(re.escape(p) for p in sorted(prefixos, key=len, reverse=True))
    return re.compile(rf"^(?P<rotulo>(?:{alternativas})\s*{_NUMERO}){_RESTO}$")


def _dispositivo(
    linha: LinhaFonte,
    artigo: re.Pattern[str],
    perfil: Perfil,
    estado: _Estado,
    relatorio: Relatorio,
) -> bool:
    """Abre o dispositivo que a linha começa; `False` quando ela não começa nenhum."""
    texto = linha.texto
    if casamento := artigo.match(texto):
        numero, sufixo = chave_de_texto(casamento["numero"])
        em = _Em(
            id=id_artigo(numero, sufixo),
            tipo="artigo",
            origem=linha.origem,
            rotulo=casamento["rotulo"],
            numero=numero,
            sufixo=sufixo,
        )
        estado.artigos.append(em)
        estado.paragrafo = estado.inciso = estado.alinea = None
    elif estado.artigo is None:
        return False
    elif casamento := _PARAGRAFO.match(texto) or _PARAGRAFO_UNICO.match(texto):
        pai = estado.artigo
        if "numero" in casamento.groupdict():
            numero, sufixo = chave_de_texto(casamento["numero"])
            id_ = id_paragrafo(pai.id, numero, sufixo)
        else:
            id_ = id_paragrafo(pai.id, None)
        em = _Em(id=id_, tipo="paragrafo", origem=linha.origem, rotulo=casamento["rotulo"])
        pai.filhos.append(em)
        estado.paragrafo, estado.inciso, estado.alinea = em, None, None
    elif (casamento := _INCISO.match(texto)) and _romano_valido(casamento["romano"]):
        pai = estado.paragrafo or estado.artigo
        em = _Em(
            id=id_inciso(pai.id, casamento["romano"]),
            tipo="inciso",
            origem=linha.origem,
            rotulo=casamento["romano"],
        )
        pai.filhos.append(em)
        estado.inciso, estado.alinea = em, None
    elif casamento := _ALINEA.match(texto):
        # Sem inciso aberto, a alínea é do parágrafo ou do caput.
        pai = estado.inciso or estado.paragrafo or estado.artigo
        em = _Em(
            id=id_alinea(pai.id, casamento["letra"]),
            tipo="alinea",
            origem=linha.origem,
            rotulo=casamento["letra"],
        )
        pai.filhos.append(em)
        estado.alinea = em
    elif perfil.pena and (casamento := _PENA.match(texto)):
        # H14: a pena é do parágrafo ou do caput e não fecha o parágrafo; o inciso seguinte
        # (art. 121, § 2º, VII depois da pena do V) continua no mesmo pai.
        pai = estado.paragrafo or estado.artigo
        pai.penas += 1
        em = _Em(id=id_pena(pai.id, pai.penas), tipo="pena", origem=linha.origem)
        pai.filhos.append(em)
        estado.inciso = estado.alinea = None
    else:
        return False
    em.acrescentar(*extrair_notas(casamento["texto"], perfil, linha.origem, relatorio))
    estado.corrente = em
    return True


def _romano_valido(romano: str) -> bool:
    try:
        id_inciso("", romano)
    except ValueError:
        return False
    return True


def _continuacao(linha: LinhaFonte, perfil: Perfil, estado: _Estado, relatorio: Relatorio) -> None:
    """RF11: o texto e as notas da linha vão para o dispositivo corrente."""
    if estado.corrente is None:
        relatorio.registrar(
            EntradaRelatorio(tipo="nao_classificada", origem=linha.origem, texto=linha.texto)
        )
        return
    estado.corrente.acrescentar(*extrair_notas(linha.texto, perfil, linha.origem, relatorio))
