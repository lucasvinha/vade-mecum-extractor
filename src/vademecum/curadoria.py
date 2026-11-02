"""Curadoria do vade mecum (`curadoria-vm/1`): leitura e validação contra os recortes.

Etapa pura: recebe o JSON já lido e os recortes, sem I/O. A curadoria é a parte da Etapa 3 que a
LLM escreve (ADR-006): marcas, atenções, quadros e avisos de capa, ancorados pela chave
`<norma>:<id>`. O esquema e as regras estão em negocio/vade-mecum.
"""

import re
import unicodedata
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from vademecum.modelo import Base, ErroFonte, No

SCHEMA = "curadoria-vm/1"
CATEGORIAS = ("verbo", "sujeito", "especializante", "quantidade", "condicao")
TETO_MARCAS = 0.15  # fração dos caracteres do artigo, sem a pena (estilo.md)


@dataclass(frozen=True, slots=True)
class Problema:
    """Uma linha de erro ou aviso do `renderizar`: `<onde>: <motivo>`."""

    onde: str
    motivo: str

    def __str__(self) -> str:
        return f"{self.onde}: {self.motivo}"


@dataclass(frozen=True, slots=True)
class Marca:
    """Trecho marcado, em posições do `texto` do nó como está no recorte (não do NFC)."""

    inicio: int
    fim: int
    cat: str


@dataclass(frozen=True, slots=True)
class Dispositivo:
    marcas: tuple[Marca, ...] = ()  # ordenadas por posição, sem sobreposição
    atencao: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CelulaPena:
    """Célula de quadro ancorada numa pena; `texto` é o do quadro ou, na literal, o do recorte."""

    pena: str  # chave `<norma>:<id>`
    texto: str


@dataclass(frozen=True, slots=True)
class Quadro:
    depois_de: str  # chave `<norma>:<id>`
    titulo: str
    colunas: tuple[str, ...]
    linhas: tuple[tuple[str | CelulaPena, ...], ...]
    nota: str | None = None


@dataclass(frozen=True, slots=True)
class Curadoria:
    edital: str
    materia: str
    gerado_em: str  # data da capa, nunca do relógio (RNF03)
    dispositivos: Mapping[str, Dispositivo]  # chave `<norma>:<id>`
    avisos_capa: tuple[str, ...] = ()
    quadros: tuple[Quadro, ...] = ()


@dataclass(frozen=True, slots=True)
class Validacao:
    """A curadoria pronta para o render, com os erros (sai 1) e os avisos (sai 0)."""

    curadoria: Curadoria
    erros: tuple[Problema, ...]
    avisos: tuple[Problema, ...]


# --- Pena ------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Pena:
    """O que se confere de uma pena: espécie, faixa com a unidade de cada ponta e multa."""

    especie: str
    minimo: tuple[int, str]
    maximo: tuple[int, str]
    multa: str  # "ausente" | "cumulativa" | "alternativa"


_UNIDADES = {"dia": "dia", "dias": "dia", "mês": "mes", "mes": "mes", "meses": "mes"}
_UNIDADES |= {"ano": "ano", "anos": "ano"}
_UNIDADE = r"(dias?|m[eê]s|meses|anos?)"
_NUMERAIS = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "quatro": 4, "cinco": 5, "seis": 6,
    "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12, "treze": 13,
    "catorze": 14, "quatorze": 14, "quinze": 15, "dezesseis": 16, "dezessete": 17,
    "dezoito": 18, "dezenove": 19,
}  # fmt: skip
_DEZENAS = {"vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50}
_EXTENSO = re.compile(
    rf"\b(?:({'|'.join(_DEZENAS)})(?:\s+e\s+({'|'.join(_NUMERAIS)}))?|({'|'.join(_NUMERAIS)}))\b"
)
# "2 (dois)", "40 (quarenta anos)" (art. 121, § 2º-D): o extenso entre parênteses repete o número.
_ALGARISMO_E_EXTENSO = re.compile(r"(\d+)\s*\(([^)]*)\)")
_ESPECIE = re.compile(r"\s*(reclusão|detenção|prisão simples)\b")
_FAIXA = re.compile(rf"(\d+)\s*{_UNIDADE}?\s+a\s+(\d+)\s*{_UNIDADE}\b")
_MULTA_ALTERNATIVA = re.compile(r"\bou\s+multa\b")
_MULTA_CUMULATIVA = re.compile(r"(?:\be|\balém\s+da)\s+multa\b")


def _numero_do_extenso(m: re.Match[str]) -> str:
    if m[3]:
        return str(_NUMERAIS[m[3]])
    return str(_DEZENAS[m[1]] + (_NUMERAIS[m[2]] if m[2] else 0))


def _sem_extenso_repetido(m: re.Match[str]) -> str:
    resto = _EXTENSO.sub("", m[2]).replace(" e ", " ").strip()
    return f"{m[1]} {resto}" if resto else m[1]


def interpretar_pena(texto: str) -> Pena | None:
    """A pena de `texto`, em forma de recorte ou de quadro; `None` quando não se interpreta.

    "dois", "2" e "2 (dois)" valem o mesmo. Duas faixas (art. 299), nenhuma (remissão do art. 304)
    ou "multa" sem "e"/"ou"/"além da" antes dão `None`: a célula do quadro usa a pena literal.
    Oração depois da faixa ("se o fato não constitui crime mais grave") não é conferida.
    """
    t = unicodedata.normalize("NFC", texto).lower()
    t = _ALGARISMO_E_EXTENSO.sub(_sem_extenso_repetido, t)
    t = _EXTENSO.sub(_numero_do_extenso, t)
    especie = _ESPECIE.match(t)
    faixas = list(_FAIXA.finditer(t))
    if especie is None or len(faixas) != 1:
        return None
    faixa = faixas[0]
    antes, depois = t[: faixa.start()], t[faixa.end() :]
    if "multa" in antes:
        return None
    if _MULTA_ALTERNATIVA.search(depois):
        multa = "alternativa"
    elif _MULTA_CUMULATIVA.search(depois):
        multa = "cumulativa"
    elif "multa" in depois:
        return None
    else:
        multa = "ausente"
    unidade_max = _UNIDADES[faixa[4]]
    unidade_min = _UNIDADES[faixa[2]] if faixa[2] else unidade_max
    return Pena(especie[1], (int(faixa[1]), unidade_min), (int(faixa[3]), unidade_max), multa)


# --- Validação -------------------------------------------------------------------------------


def _nos(nos: Sequence[No]) -> Iterator[No]:
    for no in nos:
        yield no
        yield from _nos(no.filhos)


def exigir_normas_distintas(recortes: Sequence[Base]) -> None:
    """`ErroFonte` com dois recortes da mesma norma: o segundo esconderia o primeiro (RNF04)."""
    vistas: set[str] = set()
    for recorte in recortes:
        if recorte.norma.id in vistas:
            raise ErroFonte(f"recorte repetido da norma {recorte.norma.id!r}")
        vistas.add(recorte.norma.id)


def _indice(recortes: Sequence[Base]) -> dict[str, tuple[No, No]]:
    """Chave `<norma>:<id>` → (nó, artigo do nó)."""
    exigir_normas_distintas(recortes)
    return {
        f"{recorte.norma.id}:{no.id}": (no, artigo)
        for recorte in recortes
        for artigo in recorte.artigos
        for no in _nos((artigo,))
    }


def _posicoes_originais(texto: str) -> list[int]:
    """Para cada posição do NFC de `texto`, a posição correspondente no próprio `texto`."""
    nfc = unicodedata.normalize("NFC", texto)
    if nfc == texto:
        return list(range(len(texto) + 1))
    mapa = [0] * (len(nfc) + 1)
    # Fica a maior posição: o acento combinante (NFD) vai com a letra que o precede, e a marca
    # que termina nela o leva, em vez de deixá-lo para a marca seguinte.
    for i in range(len(texto) + 1):
        mapa[len(unicodedata.normalize("NFC", texto[:i]))] = i
    return mapa


def _exigir(dados: Mapping[str, Any], chave: str, tipo: type, onde: str) -> Any:
    valor = dados.get(chave)
    if not isinstance(valor, tipo):
        raise ErroFonte(f"curadoria inválida: {onde}.{chave} ausente ou de tipo errado")
    return valor


def _lista(dados: Mapping[str, Any], chave: str, tipo: type, onde: str) -> tuple[Any, ...]:
    """A lista opcional `chave`, com cada elemento do `tipo`; vazia quando ausente."""
    valor = dados.get(chave, [])
    if not isinstance(valor, list) or not all(isinstance(v, tipo) for v in valor):
        nome = "objetos" if tipo is Mapping else "textos"
        raise ErroFonte(f"curadoria inválida: {onde}.{chave} não é lista de {nome}")
    return tuple(valor)


def _marcas(
    chave: str, no: No, brutas: Sequence[Mapping[str, Any]], erros: list[Problema]
) -> list[Marca]:
    nfc = unicodedata.normalize("NFC", no.texto)
    mapa = _posicoes_originais(no.texto)
    marcas: list[Marca] = []
    for bruta in brutas:
        trecho = unicodedata.normalize("NFC", _exigir(bruta, "trecho", str, chave))
        cat = _exigir(bruta, "cat", str, chave)
        if cat not in CATEGORIAS:
            erros.append(Problema(chave, f"cat fora da lista: {cat!r}"))
            continue
        inicio = nfc.find(trecho) if trecho else -1
        if inicio < 0:
            erros.append(Problema(chave, f"trecho não encontrado: {trecho!r}"))
        elif nfc.find(trecho, inicio + 1) >= 0:
            erros.append(Problema(chave, f"trecho ambíguo: {trecho!r}"))
        else:
            marca = Marca(mapa[inicio], mapa[inicio + len(trecho)], cat)
            if any(m.inicio < marca.fim and marca.inicio < m.fim for m in marcas):
                erros.append(Problema(chave, f"trecho sobreposto a outra marca: {trecho!r}"))
            else:
                marcas.append(marca)
    return sorted(marcas, key=lambda m: m.inicio)


def _teto(
    dispositivos: Mapping[str, Dispositivo], indice: Mapping[str, tuple[No, No]]
) -> list[Problema]:
    """Aviso por artigo cujas marcas passam de ~15% dos caracteres, sem contar a pena."""
    marcado: dict[str, int] = {}
    for chave, dispositivo in dispositivos.items():
        no, artigo = indice[chave]
        if no.tipo != "pena":
            norma = chave.split(":", 1)[0]
            artigo_chave = f"{norma}:{artigo.id}"
            soma = sum(m.fim - m.inicio for m in dispositivo.marcas)
            marcado[artigo_chave] = marcado.get(artigo_chave, 0) + soma
    avisos = []
    for artigo_chave, soma in marcado.items():
        artigo = indice[artigo_chave][0]
        total = sum(len(no.texto) for no in _nos((artigo,)) if no.tipo != "pena")
        if total and soma / total > TETO_MARCAS:
            motivo = f"marcas cobrem {soma / total:.0%} do artigo (teto ~{TETO_MARCAS:.0%})"
            avisos.append(Problema(artigo_chave, motivo))
    return avisos


def _celula(
    bruta: Any, onde: str, indice: Mapping[str, tuple[No, No]], erros: list[Problema]
) -> str | CelulaPena:
    if isinstance(bruta, str):
        return bruta
    if not isinstance(bruta, Mapping):
        raise ErroFonte(f"curadoria inválida: célula de {onde} não é texto nem pena")
    chave = _exigir(bruta, "pena", str, onde)
    texto = bruta.get("texto")
    if texto is not None and not isinstance(texto, str):
        raise ErroFonte(f"curadoria inválida: {onde}.texto de tipo errado")
    achado = indice.get(chave)
    if achado is None or achado[0].tipo != "pena":
        erros.append(Problema(onde, f"pena inexistente no recorte: {chave}"))
        return CelulaPena(chave, texto or "")
    recorte = achado[0].texto
    if texto is None:
        return CelulaPena(chave, recorte)  # pena literal: sai sem conferência
    no_quadro, no_recorte = interpretar_pena(texto), interpretar_pena(recorte)
    if no_recorte is None:
        motivo = f"pena do recorte não interpretável, use a pena literal (sem texto): {recorte!r}"
        erros.append(Problema(f"{onde}: {chave}", motivo))
    elif no_quadro is None:
        erros.append(Problema(f"{onde}: {chave}", f"pena do quadro não interpretável: {texto!r}"))
    elif no_quadro != no_recorte:
        motivo = f"pena divergente: no quadro {texto!r}, no recorte {recorte!r}"
        erros.append(Problema(f"{onde}: {chave}", motivo))
    return CelulaPena(chave, texto)


def _quadro(
    bruto: Any, numero: int, indice: Mapping[str, tuple[No, No]], erros: list[Problema]
) -> Quadro:
    onde = f"quadro {numero}"
    if not isinstance(bruto, Mapping):
        raise ErroFonte(f"curadoria inválida: {onde} não é objeto")
    depois_de = _exigir(bruto, "depois_de", str, onde)
    if depois_de not in indice:
        erros.append(Problema(onde, f"depois_de inexistente no recorte: {depois_de}"))
    _exigir(bruto, "colunas", list, onde)
    colunas = _lista(bruto, "colunas", str, onde)
    linhas = []
    for n, linha in enumerate(_exigir(bruto, "linhas", list, onde), start=1):
        if not isinstance(linha, list) or len(linha) != len(colunas):
            raise ErroFonte(f"curadoria inválida: {onde}, linha {n}, fora do número de colunas")
        linhas.append(tuple(_celula(c, f"{onde}, linha {n}", indice, erros) for c in linha))
    nota = bruto.get("nota")
    if nota is not None and not isinstance(nota, str):
        raise ErroFonte(f"curadoria inválida: {onde}.nota de tipo errado")
    return Quadro(depois_de, _exigir(bruto, "titulo", str, onde), colunas, tuple(linhas), nota)


def validar_curadoria(dados: Mapping[str, Any], recortes: Sequence[Base]) -> Validacao:
    """A curadoria validada contra os recortes (ADR-006; regras em negocio/vade-mecum).

    Esquema ou forma errada (chave ausente, tipo trocado) é erro de entrada: `ErroFonte`. O que
    não casa com os recortes (id, trecho, `cat`, pena) vai para `erros`, um por problema, na ordem
    do arquivo; o teto de marcas vai para `avisos`.
    """
    if not isinstance(dados, Mapping) or dados.get("schema") != SCHEMA:
        raise ErroFonte(f"curadoria sem o esquema {SCHEMA}")
    indice = _indice(recortes)
    erros: list[Problema] = []
    dispositivos: dict[str, Dispositivo] = {}
    for chave, bruto in _exigir(dados, "dispositivos", Mapping, "curadoria").items():
        if not isinstance(bruto, Mapping):
            raise ErroFonte(f"curadoria inválida: dispositivos.{chave} não é objeto")
        if chave not in indice:
            erros.append(Problema(chave, "id inexistente no recorte"))
            continue
        brutas = _lista(bruto, "marcas", Mapping, chave)
        marcas = _marcas(chave, indice[chave][0], brutas, erros)
        dispositivos[chave] = Dispositivo(tuple(marcas), _lista(bruto, "atencao", str, chave))
    quadros = tuple(
        _quadro(bruto, n, indice, erros)
        for n, bruto in enumerate(dados.get("quadros", ()), start=1)
    )
    curadoria = Curadoria(
        edital=_exigir(dados, "edital", str, "curadoria"),
        materia=_exigir(dados, "materia", str, "curadoria"),
        gerado_em=_exigir(dados, "gerado_em", str, "curadoria"),
        avisos_capa=_lista(dados, "avisos_capa", str, "curadoria"),
        dispositivos=dispositivos,
        quadros=quadros,
    )
    return Validacao(curadoria, tuple(erros), tuple(_teto(dispositivos, indice)))
