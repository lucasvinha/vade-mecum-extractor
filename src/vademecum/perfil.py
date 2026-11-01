"""Perfil da norma: `padrao.toml` mesclado com o perfil específico (ADR-002).

Tudo o que varia entre normas mora no perfil; o parser não sabe qual norma lê. As chaves e o que
cada uma muda estão em negocio/pipeline-e-perfis. Chave desconhecida é erro: um erro de digitação
no `.toml` desligaria uma regra em silêncio.
"""

import tomllib
from dataclasses import dataclass
from importlib import resources
from typing import Any

from vademecum.modelo import ErroFonte

_PADRAO = "padrao"

# Chaves aceitas por tabela; `None` marca a chave da raiz. `notas` aceita qualquer tipo de nota.
_CHAVES = {
    None: {"id", "artigo", "hierarquia", "dispositivos", "rubrica", "rodape", "validacao", "notas"},
    "artigo": {"prefixos"},
    "hierarquia": {"niveis"},
    "dispositivos": {"rubrica", "pena"},
    "rubrica": {"sem_negrito"},
    "rodape": {"inicio"},
    "validacao": {"lacunas"},
}


@dataclass(frozen=True, slots=True)
class Perfil:
    """Regras de uma norma, já mescladas com o padrão."""

    id: str
    prefixos_artigo: tuple[str, ...]  # P9
    niveis: tuple[str, ...]  # palavras-chave dos níveis, na ordem (H5)
    rubrica: bool
    pena: bool
    rubrica_sem_negrito: bool  # heurística (c) da H6
    rodape_inicio: tuple[str, ...]  # regex da linha que abre o rodapé (H17)
    lacunas: bool  # V2
    notas: tuple[tuple[str, tuple[str, ...]], ...]  # (tipo, gatilhos), na ordem do `.toml`


def carregar_perfil(nome: str) -> Perfil:
    """Perfil `nome` sobre o `padrao`; perfil inexistente ou chave desconhecida é `ErroFonte`."""
    dados = _ler(_PADRAO)
    if nome != _PADRAO:
        dados = _mesclar(dados, _ler(nome))
    return Perfil(
        id=dados["id"],
        prefixos_artigo=tuple(dados["artigo"]["prefixos"]),
        niveis=tuple(dados["hierarquia"]["niveis"]),
        rubrica=dados["dispositivos"]["rubrica"],
        pena=dados["dispositivos"]["pena"],
        rubrica_sem_negrito=dados["rubrica"]["sem_negrito"],
        rodape_inicio=tuple(dados["rodape"]["inicio"]),
        lacunas=dados["validacao"]["lacunas"],
        notas=tuple((tipo, tuple(gatilhos)) for tipo, gatilhos in dados["notas"].items()),
    )


def _ler(nome: str) -> dict[str, Any]:
    arquivo = resources.files("vademecum.perfis") / f"{nome}.toml"
    if not arquivo.is_file():
        raise ErroFonte(f"perfil inexistente: {nome!r}")
    dados = tomllib.loads(arquivo.read_text(encoding="utf-8"))
    _validar(dados, nome)
    return dados


def _validar(dados: dict[str, Any], nome: str) -> None:
    desconhecidas = [chave for chave in dados if chave not in _CHAVES[None]]
    for tabela, aceitas in _CHAVES.items():
        if tabela is not None and isinstance(dados.get(tabela), dict):
            desconhecidas += [f"{tabela}.{c}" for c in dados[tabela] if c not in aceitas]
    if desconhecidas:
        raise ErroFonte(f"chave desconhecida no perfil {nome!r}: {', '.join(desconhecidas)}")


def _mesclar(base: dict[str, Any], especifico: dict[str, Any]) -> dict[str, Any]:
    """O específico sobrescreve só as chaves que traz; tabela se mescla, lista se troca inteira."""
    resultado = dict(base)
    for chave, valor in especifico.items():
        if isinstance(valor, dict) and isinstance(base.get(chave), dict):
            resultado[chave] = {**base[chave], **valor}
        else:
            resultado[chave] = valor
    return resultado
