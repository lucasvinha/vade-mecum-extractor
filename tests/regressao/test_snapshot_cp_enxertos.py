"""Regressão: a base e o relatório dos enxertos do CP contra o snapshot versionado (PADRAO_OURO).

Só o `.mht` entra: o `capturado_em` dele vem do `Date` da captura, e o do `.htm` é o `mtime`, que
muda a cada checkout. A fonte vai relativa à raiz para o `norma.fonte` não variar entre máquinas.
Snapshot divergente se revisa e, se a mudança for a esperada, se regrava com o mesmo `extrair`
(`--saida tests/fixtures/snapshots/cp_enxertos.json`), com a justificativa no corpo do commit.
"""

from pathlib import Path

import pytest

from vademecum.cli import main

pytestmark = pytest.mark.regressao

RAIZ = Path(__file__).resolve().parents[2]
FONTE = "tests/fixtures/html/cp_enxertos.mht"
SNAPSHOTS = RAIZ / "tests" / "fixtures" / "snapshots"


@pytest.mark.parametrize("arquivo", ["cp_enxertos.json", "cp_enxertos.relatorio.json"])
def test_snapshot_cp_enxertos(arquivo, tmp_path, monkeypatch):
    monkeypatch.chdir(RAIZ)
    saida = tmp_path / "cp_enxertos.json"
    assert main(["extrair", "--fonte", FONTE, "--perfil", "cp", "--saida", str(saida)]) == 0
    assert (tmp_path / arquivo).read_bytes() == (SNAPSHOTS / arquivo).read_bytes()
