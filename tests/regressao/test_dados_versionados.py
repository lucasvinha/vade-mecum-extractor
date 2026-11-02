"""Sincronia: as bases e os recortes versionados em `dados/` saem iguais, byte a byte (ADR-005).

A fonte de `dados/bases/<norma>/` é o `.mht` de `dados/fontes/<norma>/` (ADR-005): o
`capturado_em` dele vem do `Date` da captura, e o do `.htm` é o `mtime`, que muda a cada
checkout. O perfil é o que a própria base registra em `norma.perfil`. O recorte
`dados/recortes/<edital>/<materia>/<norma>.json` sai da base da norma e dos tópicos do edital.
Divergente, se regrava com o mesmo comando, com a justificativa no corpo do commit.
"""

import json
from pathlib import Path

import pytest

from vademecum.cli import main

pytestmark = pytest.mark.regressao

RAIZ = Path(__file__).resolve().parents[2]
BASES = RAIZ / "dados" / "bases"
FONTES = RAIZ / "dados" / "fontes"
RECORTES = RAIZ / "dados" / "recortes"
NORMAS = sorted(pasta.name for pasta in BASES.iterdir() if pasta.is_dir())
TOPICOS = {"oj26": RAIZ / "claude" / "topicos-oj2026.json"}
RECORTES_VERSIONADOS = sorted(
    caminho.relative_to(RECORTES).as_posix()
    for caminho in RECORTES.glob("*/*/*.json")
    if not caminho.name.endswith(".relatorio.json")
)


def test_ha_base_versionada():
    assert NORMAS, f"nenhuma base em {BASES.relative_to(RAIZ)}"


@pytest.mark.parametrize("norma", NORMAS)
def test_base_versionada_bate_com_a_fonte(norma, tmp_path):
    versionada = BASES / norma / "base.json"
    perfil = json.loads(versionada.read_text(encoding="utf-8"))["norma"]["perfil"]
    [fonte] = sorted((FONTES / norma).glob("*.mht"))
    saida = tmp_path / "base.json"
    assert main(["extrair", "--fonte", str(fonte), "--perfil", perfil, "--saida", str(saida)]) == 0
    for arquivo in ("base.json", "base.relatorio.json"):
        assert (tmp_path / arquivo).read_bytes() == (BASES / norma / arquivo).read_bytes(), arquivo


@pytest.mark.parametrize("recorte", RECORTES_VERSIONADOS)
def test_recorte_versionado_bate_com_a_base_e_os_topicos(recorte, tmp_path):
    edital, materia, arquivo = recorte.split("/")
    norma = arquivo.removesuffix(".json")
    saida = tmp_path / arquivo
    argv = ["recortar", "--base", str(BASES / norma / "base.json"), "--saida", str(saida)]
    assert main([*argv, "--topicos", str(TOPICOS[edital]), "--materia", materia]) == 0
    for nome in (arquivo, f"{norma}.relatorio.json"):
        assert (tmp_path / nome).read_bytes() == (RECORTES / edital / materia / nome).read_bytes()
