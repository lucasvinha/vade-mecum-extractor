import re
from pathlib import Path

import pytest

from vademecum.fontes.html import ler_html
from vademecum.modelo import Relatorio
from vademecum.normalizador import normalizar

pytestmark = pytest.mark.aceite


@pytest.fixture
def textos(fixtures_dir: Path) -> list[str]:
    linhas = ler_html(fixtures_dir / "html" / "cp_enxertos.mht", Relatorio()).linhas
    return [linha.texto for linha in normalizar(linhas, ("Art.", "Art"))]


def test_a8_paragrafos_rotulados_com_indicador_ordinal(textos):
    assert any(t.startswith("§ 4º No homicídio culposo") for t in textos)  # `§ 4o`, art. 121
    # `§ 2°` do art. 78
    assert any(t.startswith("§ 2º Se o condenado houver reparado o dano") for t in textos)
    assert any(t.startswith("§ 2º Se o homicídio é cometido:") for t in textos)  # `§ 2°`, art. 121
    assert "§ 2º-A (Revogado pela Lei nº 14.994, de 2024)" in textos


def test_a8_nenhum_rotulo_com_o_ou_grau_sobra(textos):
    assert [t for t in textos if re.match(r"(?:§|Art\.?)\s*\d+[o°](?!\w)", t)] == []
