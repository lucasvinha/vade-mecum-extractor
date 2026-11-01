"""Parser: linhas normalizadas → árvore artigo › parágrafo › inciso › alínea (ver negocio/parsing).

Etapa pura, máquina de estados sobre as linhas. Os prefixos de artigo vêm do perfil (ADR-002, P9);
os regex partem da tabela de negocio/parsing e rodam depois do `normalizador`, com ordinal em `º`
e separador em `-`. As notas saem do texto por `notas.extrair_notas` (RF12).
"""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field, fields

from vademecum.modelo import (
    EntradaRelatorio,
    LinhaFonte,
    Local,
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
# H6 (c): o resto da rubrica sem negrito não termina em pontuação de frase.
_PONTUADO = (".", ";", ":", ",")
# RF11, RF14: o tipo de nota que, abrindo linha sem rótulo, a descarta.
_VETO = "veto"
# H5: campos de `Local` que são nível; a palavra-chave do perfil, sem acento, dá o campo.
_NIVEIS = tuple(f.name for f in fields(Local) if f.name != "rotulo_livre")
_SEPARADOR_NOME = " — "  # `TÍTULO I — DOS CRIMES CONTRA A PESSOA`


@dataclass(slots=True)
class _Em:
    """Nó em construção; vira `No` congelado no fim."""

    id: str
    tipo: str
    origem: str
    rotulo: str | None = None
    rubrica: str | None = None
    local: Local | None = None
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
            rubrica=self.rubrica,
            local=self.local,
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
    # Rubrica à espera do dispositivo seguinte (H6, H7): a linha, o texto e as notas.
    rubrica: tuple[LinhaFonte, str, tuple[Nota, ...]] | None = None
    local: dict[str, str | None] = field(default_factory=dict)  # campos de `Local` (H5)

    @property
    def artigo(self) -> _Em | None:
        return self.artigos[-1] if self.artigos else None


def analisar(linhas: Iterable[LinhaFonte], perfil: Perfil, relatorio: Relatorio) -> tuple[No, ...]:
    """Artigos na ordem da fonte, com `local`, parágrafos, incisos, alíneas, penas e rubricas.

    RF07–RF11, H5–H7, H14, H18. Linha sem dispositivo aberto que a receba vai ao relatório como
    `nao_classificada` (V7, RNF04).
    """
    artigo = _padrao_artigo(perfil.prefixos_artigo)
    estado = _Estado()
    linhas = [linha for linha in linhas if linha.texto]
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if linha.centralizado and (campo := _campo_nivel(linha.texto, perfil.niveis)):
            _rubrica_sem_dispositivo(estado, relatorio)
            i = _nivel(linhas, i, campo, artigo, perfil, estado, relatorio)
            continue
        i += 1
        casado = _casar(linha.texto, artigo, perfil)
        seguinte = linhas[i] if i < len(linhas) else None
        if casado is None and _e_rubrica(linha, seguinte, artigo, perfil):
            _rubrica_sem_dispositivo(estado, relatorio)
            estado.rubrica = (linha, *extrair_notas(linha.texto, perfil, linha.origem, relatorio))
            continue
        if casado is None and linha.centralizado and linha.negrito and estado.artigos:
            _rubrica_sem_dispositivo(estado, relatorio)
            _rotulo_livre(linha, perfil, estado, relatorio)
            continue
        em = _abrir(casado, linha, perfil, estado, relatorio) if casado else None
        if em is not None and em.tipo != "pena" and estado.rubrica is not None:
            # H7: a nota da rubrica vem antes das notas do dispositivo.
            _, em.rubrica, notas = estado.rubrica
            em.notas[:0] = notas
            estado.rubrica = None
        _rubrica_sem_dispositivo(estado, relatorio)
        if em is None:
            _continuacao(linha, perfil, estado, relatorio)
    _rubrica_sem_dispositivo(estado, relatorio)
    return tuple(em.congelar() for em in estado.artigos)


def _campo_nivel(texto: str, niveis: Iterable[str]) -> str | None:
    """H5: o campo de `Local` da palavra-chave que abre a linha, sem diferenciar maiúsculas."""
    dobrado = texto.casefold()
    for palavra in niveis:
        chave = palavra.casefold()
        if dobrado.startswith(chave) and not dobrado[len(chave) : len(chave) + 1].isalnum():
            campo = "".join(
                c for c in unicodedata.normalize("NFD", chave) if not unicodedata.combining(c)
            )
            if campo not in _NIVEIS:
                raise ValueError(f"nível do perfil sem campo em `Local`: {palavra!r}")
            return campo
    return None


def _nivel(
    linhas: list[LinhaFonte],
    i: int,
    campo: str,
    artigo: re.Pattern[str],
    perfil: Perfil,
    estado: _Estado,
    relatorio: Relatorio,
) -> int:
    """Lê o nível em `linhas[i]` e o nome nas centralizadas seguintes; devolve a próxima linha.

    H5: o nome são as centralizadas que não são nota, nível nem rubrica (H6 d), unidas por espaço
    (`DOS CRIMES CONTRA A` / `INVIOLABILIDADE DE CORRESPONDÊNCIA`). H18: a nota do nível, antes ou
    depois do nome, não tem nó onde ficar e vira `aviso`. O nível novo zera os de baixo.
    """
    rotulo = _sem_notas(linhas[i], perfil, relatorio)
    nomes: list[str] = []
    j = i + 1
    while j < len(linhas) and linhas[j].centralizado:
        linha = linhas[j]
        seguinte = linhas[j + 1] if j + 1 < len(linhas) else None
        if _campo_nivel(linha.texto, perfil.niveis) or _e_rubrica(linha, seguinte, artigo, perfil):
            break
        if nome := _sem_notas(linha, perfil, relatorio):
            nomes.append(nome)
        j += 1
    abaixo = _NIVEIS[_NIVEIS.index(campo) + 1 :]
    estado.local.update(dict.fromkeys(abaixo), rotulo_livre=None)
    estado.local[campo] = _SEPARADOR_NOME.join([rotulo, " ".join(nomes)]) if nomes else rotulo
    estado.corrente = None
    return j


def _rotulo_livre(linha: LinhaFonte, perfil: Perfil, estado: _Estado, relatorio: Relatorio) -> None:
    """H5, P8: centralizada em negrito sem palavra-chave depois do primeiro artigo
    (`DISPOSIÇÕES FINAIS`). Fecha os níveis abaixo da parte: não pertence ao título aberto
    (operador, 2026-11-01).
    """
    estado.local.update(
        dict.fromkeys(_NIVEIS[1:]), rotulo_livre=_sem_notas(linha, perfil, relatorio)
    )
    estado.corrente = None


def _sem_notas(linha: LinhaFonte, perfil: Perfil, relatorio: Relatorio) -> str:
    """Texto de linha de nível sem as notas; a linha que tinha nota vai ao relatório (H18)."""
    limpo, notas = extrair_notas(linha.texto, perfil, linha.origem, relatorio)
    if notas:
        relatorio.registrar(EntradaRelatorio(tipo="aviso", origem=linha.origem, texto=linha.texto))
    return limpo


def _padrao_artigo(prefixos: Iterable[str]) -> re.Pattern[str]:
    # O mais longo primeiro, como no normalizador: `Artigo` antes de `Art` (P9).
    alternativas = "|".join(re.escape(p) for p in sorted(prefixos, key=len, reverse=True))
    return re.compile(rf"^(?P<rotulo>(?:{alternativas})\s*{_NUMERO}){_RESTO}$")


def _casar(texto: str, artigo: re.Pattern[str], perfil: Perfil) -> tuple[str, re.Match[str]] | None:
    """O tipo de dispositivo que a linha começa, só pelo padrão, sem olhar o estado."""
    if casamento := artigo.match(texto):
        return "artigo", casamento
    if casamento := _PARAGRAFO.match(texto) or _PARAGRAFO_UNICO.match(texto):
        return "paragrafo", casamento
    if (casamento := _INCISO.match(texto)) and _romano_valido(casamento["romano"]):
        return "inciso", casamento
    if casamento := _ALINEA.match(texto):
        return "alinea", casamento
    if perfil.pena and (casamento := _PENA.match(texto)):
        return "pena", casamento
    return None


def _abrir(
    casado: tuple[str, re.Match[str]],
    linha: LinhaFonte,
    perfil: Perfil,
    estado: _Estado,
    relatorio: Relatorio,
) -> _Em | None:
    """Abre o dispositivo casado; `None` quando não há artigo aberto que o receba."""
    tipo, casamento = casado
    if tipo == "artigo":
        numero, sufixo = chave_de_texto(casamento["numero"])
        em = _Em(
            id=id_artigo(numero, sufixo),
            tipo=tipo,
            origem=linha.origem,
            rotulo=casamento["rotulo"],
            numero=numero,
            sufixo=sufixo,
            local=Local(**estado.local),
        )
        estado.artigos.append(em)
        estado.paragrafo = estado.inciso = estado.alinea = None
    elif estado.artigo is None:
        return None
    elif tipo == "paragrafo":
        pai = estado.artigo
        if "numero" in casamento.groupdict():
            numero, sufixo = chave_de_texto(casamento["numero"])
            id_ = id_paragrafo(pai.id, numero, sufixo)
        else:
            id_ = id_paragrafo(pai.id, None)
        em = _Em(id=id_, tipo=tipo, origem=linha.origem, rotulo=casamento["rotulo"])
        pai.filhos.append(em)
        estado.paragrafo, estado.inciso, estado.alinea = em, None, None
    elif tipo == "inciso":
        pai = estado.paragrafo or estado.artigo
        em = _Em(
            id=id_inciso(pai.id, casamento["romano"]),
            tipo=tipo,
            origem=linha.origem,
            rotulo=casamento["romano"],
        )
        pai.filhos.append(em)
        estado.inciso, estado.alinea = em, None
    elif tipo == "alinea":
        # Sem inciso aberto, a alínea é do parágrafo ou do caput.
        pai = estado.inciso or estado.paragrafo or estado.artigo
        em = _Em(
            id=id_alinea(pai.id, casamento["letra"]),
            tipo=tipo,
            origem=linha.origem,
            rotulo=casamento["letra"],
        )
        pai.filhos.append(em)
        estado.alinea = em
    else:
        # H14: a pena é do parágrafo ou do caput e não fecha o parágrafo; o inciso seguinte
        # (art. 121, § 2º, VII depois da pena do V) continua no mesmo pai.
        pai = estado.paragrafo or estado.artigo
        pai.penas += 1
        em = _Em(id=id_pena(pai.id, pai.penas), tipo=tipo, origem=linha.origem)
        pai.filhos.append(em)
        estado.inciso = estado.alinea = None
    em.acrescentar(*extrair_notas(casamento["texto"], perfil, linha.origem, relatorio))
    estado.corrente = em
    return em


def _romano_valido(romano: str) -> bool:
    try:
        id_inciso("", romano)
    except ValueError:
        return False
    return True


def _e_rubrica(
    linha: LinhaFonte, seguinte: LinhaFonte | None, artigo: re.Pattern[str], perfil: Perfil
) -> bool:
    """H6: linha sem padrão de dispositivo nem de nível, numa das formas (a) a (d).

    Não centralizada: (a) 100% negrito; (b) só o início em negrito (`Lugar do crime (Redação
    dada…)`) e seguida de dispositivo; (c) sem negrito, se o perfil ligar, com o resto sem notas não
    pontuado (`Sabotagem`) e seguida de dispositivo. Centralizada: (d) em caixa mista e seguida de
    dispositivo (`Registro não autorizado da intimidade sexual`, CP, art. 216-B). A pena não é
    dispositivo que receba rubrica.
    """
    if not perfil.rubrica:
        return False
    # Relatório descartável: aqui só se classifica.
    # A nota `outra` entra no relatório de verdade quando a rubrica for aceita.
    limpo, _ = extrair_notas(linha.texto, perfil, linha.origem, Relatorio())
    if not limpo:
        return False
    casado = _casar(seguinte.texto, artigo, perfil) if seguinte else None
    segue_dispositivo = casado is not None and casado[0] != "pena"
    if linha.centralizado:
        # Nome de nível vem em maiúsculas ou todo em minúsculas (`das fraudes em certames…`).
        caixa_mista = any(c.isupper() for c in limpo) and any(c.islower() for c in limpo)
        return caixa_mista and segue_dispositivo
    if linha.negrito:
        return True
    if linha.rotulo_negrito:
        return segue_dispositivo
    return perfil.rubrica_sem_negrito and not limpo.endswith(_PONTUADO) and segue_dispositivo


def _rubrica_sem_dispositivo(estado: _Estado, relatorio: Relatorio) -> None:
    """H7: rubrica que não chegou a um dispositivo (veio nível, pena ou o fim) vira `aviso`."""
    if estado.rubrica is None:
        return
    linha, _, _ = estado.rubrica
    relatorio.registrar(EntradaRelatorio(tipo="aviso", origem=linha.origem, texto=linha.texto))
    estado.rubrica = None


def _continuacao(linha: LinhaFonte, perfil: Perfil, estado: _Estado, relatorio: Relatorio) -> None:
    """RF11: o texto e as notas da linha vão para o dispositivo corrente.

    Linha sem rótulo que começa por `(VETADO)` é `descarte` (RF14): não é nota de outro dispositivo.
    """
    # Sem dispositivo corrente, a linha inteira vai ao relatório: a nota `outra` não conta à parte.
    descartavel = Relatorio() if estado.corrente is None else relatorio
    limpo, notas = extrair_notas(linha.texto, perfil, linha.origem, descartavel)
    if linha.texto.startswith("(") and notas and notas[0].tipo == _VETO:
        # Vale também logo depois de um nível (CP, `p#2383`), quando não há dispositivo corrente.
        relatorio.registrar(
            EntradaRelatorio(tipo="descarte", origem=linha.origem, texto=linha.texto)
        )
    elif estado.corrente is None:
        relatorio.registrar(
            EntradaRelatorio(tipo="nao_classificada", origem=linha.origem, texto=linha.texto)
        )
    else:
        estado.corrente.acrescentar(limpo, notas)
