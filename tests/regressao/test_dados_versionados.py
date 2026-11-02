"""Sincronia: cada base versionada em `dados/bases/` sai igual, byte a byte, da fonte versionada.

A fonte de `dados/bases/<norma>/` é o `.mht` de `dados/fontes/<norma>/` (ADR-005): o
`capturado_em` dele vem do `Date` da captura, e o do `.htm` é o `mtime`, que muda a cada
checkout. O perfil é o que a própria base registra em `norma.perfil`. Base divergente se regrava
com o mesmo `extrair`, com a justificativa no corpo do commit.
"""

import json
from pathlib import Path

import pytest

from vademecum.cli import main

pytestmark = pytest.mark.regressao

RAIZ = Path(__file__).resolve().parents[2]
BASES = RAIZ / "dados" / "bases"
FONTES = RAIZ / "dados" / "fontes"
NORMAS = sorted(pasta.name for pasta in BASES.iterdir() if pasta.is_dir())


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
