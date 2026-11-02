"""Bases geradas pela CLI, de ponta a ponta, uma vez por sessão (ver docs/PADRAO_OURO.md)."""

import json
from pathlib import Path

import pytest

from vademecum.cli import main

RAIZ = Path(__file__).resolve().parents[2]
CP_INTEIRO = RAIZ / "dados" / "fontes" / "cp" / "del2848compilado.htm"


def extrair(fonte: Path, pasta: Path) -> tuple[dict, dict]:
    """`(base, relatorio)` lidos do JSON que o `extrair` gravou."""
    saida = pasta / "base.json"
    assert main(["extrair", "--fonte", str(fonte), "--perfil", "cp", "--saida", str(saida)]) == 0
    relatorio = pasta / "base.relatorio.json"
    return (
        json.loads(saida.read_text(encoding="utf-8")),
        json.loads(relatorio.read_text(encoding="utf-8")),
    )


def _no(base: dict, id_: str) -> dict:
    """O nó `id_` em qualquer nível da árvore."""
    pendentes = list(base["artigos"])
    while pendentes:
        atual = pendentes.pop()
        if atual["id"] == id_:
            return atual
        pendentes.extend(atual.get("filhos", ()))
    raise KeyError(id_)


@pytest.fixture
def no():
    """`no(base, id_)`: o nó `id_` em qualquer nível da árvore."""
    return _no


@pytest.fixture(scope="session")
def cp_parser(tmp_path_factory) -> tuple[dict, dict]:
    # Cabeçalho, arts. 1º a 3º, 88, 129, 359-I ao fim e rodapé, em bytes do `.htm`.
    fonte = RAIZ / "tests" / "fixtures" / "html" / "cp_parser.htm"
    return extrair(fonte, tmp_path_factory.mktemp("cp_parser"))


@pytest.fixture(scope="session")
def cp_enxertos(tmp_path_factory) -> tuple[dict, dict]:
    # Arts. 78, 121 a 121-B e 187 a 191, recortados do `.mht`.
    fonte = RAIZ / "tests" / "fixtures" / "html" / "cp_enxertos.mht"
    return extrair(fonte, tmp_path_factory.mktemp("cp_enxertos"))


@pytest.fixture(scope="session")
def cp_inteiro(tmp_path_factory) -> tuple[dict, dict]:
    # A fonte inteira é versionada em `dados/` (ADR-005): ausente, o A1 falha em vez de pular.
    return extrair(CP_INTEIRO, tmp_path_factory.mktemp("cp_inteiro"))
