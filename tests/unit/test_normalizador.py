from pathlib import Path

import pytest

from vademecum.fontes.html import ler_html
from vademecum.modelo import LinhaFonte, Relatorio
from vademecum.normalizador import normalizar

# Os prefixos que o perfil do CP vai passar no M3: `Art.` e `Art` sem ponto (H11, `Art 187.`).
PREFIXOS_CP = ("Art.", "Art")


@pytest.fixture
def cp(fixtures_dir: Path) -> tuple[LinhaFonte, ...]:
    return ler_html(fixtures_dir / "html" / "cp_enxertos.mht", Relatorio()).linhas


@pytest.fixture
def normalizado(cp) -> dict[str, LinhaFonte]:
    return {linha.origem: linha for linha in normalizar(cp, PREFIXOS_CP)}


def _linha(texto: str) -> LinhaFonte:
    return LinhaFonte(texto, False, False, False, None, "pdf:p1:col1:l1")


def _texto(cp, inicio: str) -> str:
    return next(linha.texto for linha in cp if linha.texto.startswith(inicio))


@pytest.mark.parametrize(
    ("antes", "depois"),
    [
        ("§ 4o No homicídio culposo", "§ 4º No homicídio culposo"),  # art. 121
        (
            "§ 2° Se o condenado houver reparado o dano",
            "§ 2º Se o condenado houver reparado o dano",
        ),
        (
            "§ 2o-A (Revogado pela Lei nº 14.994, de 2024)",
            "§ 2º-A (Revogado pela Lei nº 14.994, de 2024)",
        ),
        ("§ 7o (Revogado", "§ 7º (Revogado"),
    ],
)
def test_h11_ordinal_do_paragrafo_vira_o_indicador_ordinal(cp, antes, depois):
    texto = _texto(cp, antes)
    (linha,) = normalizar([_linha(texto)], PREFIXOS_CP)
    assert linha.texto == depois + texto[len(antes) :]


@pytest.mark.parametrize(
    ("antes", "depois"),
    [
        ("VII – contra:", "VII - contra:"),  # art. 121, § 2º
        ("I – violência doméstica", "I - violência doméstica"),  # art. 121-A, § 1º
        ("Pena – reclusão, de 20 (vinte)", "Pena - reclusão, de 20 (vinte)"),  # art. 121-A
    ],
)
def test_h13_travessao_depois_do_rotulo_vira_hifen(cp, antes, depois):
    texto = _texto(cp, antes)
    (linha,) = normalizar([_linha(texto)], PREFIXOS_CP)
    assert linha.texto == depois + texto[len(antes) :]


@pytest.mark.parametrize(
    "inicio",
    ["Art. 78 - ", "Art. 121. ", "Art 187. ", "Art. 121-A. ", "§ 1º - ", "§ 2º-B. ", "II - "],
)
def test_h11_rotulo_ja_normalizado_fica_igual(cp, inicio):
    texto = _texto(cp, inicio)
    (linha,) = normalizar([_linha(texto)], PREFIXOS_CP)
    assert linha.texto == texto


def test_h11_ordinal_no_corpo_fica_literal():
    # CP, art. 129, § 7º (`dados/cp/del2848compilado.mht`, html:p#703): fora da fixture, então o
    # texto entra literal. Só o `§ 7o` do rótulo muda; os do corpo são texto legal.
    texto = (
        "§ 7o Aumenta-se a pena de 1/3 (um terço) se ocorrer qualquer das hipóteses dos §§ 4o e "
        "6o do art. 121 deste Código. (Redação dada pela Lei nº 12.720, de 2012)"
    )
    (linha,) = normalizar([_linha(texto)], PREFIXOS_CP)
    assert linha.texto == "§ 7º" + texto[len("§ 7o") :]
    assert "dos §§ 4o e 6o do art. 121" in linha.texto


def test_h13_travessao_no_corpo_fica_literal():
    texto = "IV – em descumprimento das medidas protetivas"
    (linha,) = normalizar([_linha("Pena - reclusão; " + texto)], PREFIXOS_CP)
    assert linha.texto == "Pena - reclusão; " + texto


def test_p9_artigo_1_com_o_prefixo_passado():
    # Lei SP 11.608 (P9), que vem do PDF do M9: sem fixture HTML, o texto é o literal da P9.
    (linha,) = normalizar([_linha("Artigo 1° -")], ("Art.", "Artigo"))
    assert linha.texto == "Artigo 1º -"


def test_adr002_prefixo_nao_passado_nao_e_rotulo():
    (linha,) = normalizar([_linha("Artigo 1° -")], PREFIXOS_CP)
    assert linha.texto == "Artigo 1° -"


def test_flags_e_origem_ficam_e_a_ordem_tambem(cp, normalizado):
    assert list(normalizado) == [linha.origem for linha in cp]
    for original in cp:
        linha = normalizado[original.origem]
        assert (linha.negrito, linha.rotulo_negrito, linha.centralizado, linha.cor) == (
            original.negrito,
            original.rotulo_negrito,
            original.centralizado,
            original.cor,
        )


def test_so_o_rotulo_inicial_muda_no_trecho_inteiro(cp, normalizado):
    for original in cp:
        texto = normalizado[original.origem].texto
        assert len(texto) == len(original.texto)
        diferencas = [
            i for i, (a, b) in enumerate(zip(original.texto, texto, strict=True)) if a != b
        ]
        assert all(i < 12 for i in diferencas), (original.origem, texto)
