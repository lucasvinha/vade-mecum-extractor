import pytest

from vademecum.modelo import LinhaFonte, No, Relatorio
from vademecum.normalizador import normalizar
from vademecum.parser import analisar
from vademecum.perfil import carregar_perfil
from vademecum.vigencia import filtrar_vigentes

# Linhas reais do CP (`dados/cp/del2848compilado.mht`), com o `p#` da fonte.
ART_121_P2 = [
    (575, "Art. 121. Matar alguem:"),
    (580, "§ 2º Se o homicídio é cometido:"),
    (581, "I - mediante paga ou promessa de recompensa, ou por outro motivo torpe;"),
    (586, "Pena - reclusão, de doze a trinta anos."),
    (587, "Feminicídio (Incluído pela Lei nº 13.104, de 2015)", "rotulo"),
    (588, "VI - (Revogado pela Lei nº 14.994, de 2024)"),
    (589, "VII – contra: (Redação dada pela Lei nº 15.134, de 2025)"),
    (596, "Pena - reclusão, de doze a trinta anos."),
]
ART_171_P5 = [
    (
        1146,
        "Art. 171 - Obter, para si ou para outrem, vantagem ilícita, em prejuízo alheio, "
        "induzindo ou mantendo alguém em erro, mediante artifício, ardil, ou qualquer outro "
        "meio fraudulento:",
    ),
    (1170, "§ 5º (Revogado). (Redação dada pela Lei nº 15.397, de 2026)"),
    (1171, "I – (Revogado); (Redação dada pela Lei nº 15.397, de 2026)"),
    (1172, "II – (Revogado); (Redação dada pela Lei nº 15.397, de 2026)"),
    (1173, "III – (Revogado); (Redação dada pela Lei nº 15.397, de 2026)"),
    (1174, "IV – (Revogado). (Redação dada pela Lei nº 15.397, de 2026)"),
]


@pytest.fixture(scope="module")
def cp():
    return carregar_perfil("cp")


def _artigos(pares, perfil):
    """`(p, texto)` ou `(p, texto, "rotulo")`, como em `test_parser.py`, já analisados."""
    linhas = [
        LinhaFonte(
            texto=par[1],
            negrito=False,
            rotulo_negrito="rotulo" in par[2:],
            centralizado=False,
            cor=None,
            origem=f"html:p#{par[0]}",
        )
        for par in pares
    ]
    return analisar(normalizar(linhas, perfil.prefixos_artigo), perfil, Relatorio()).artigos


def _filtrar(pares, perfil):
    relatorio = Relatorio()
    return filtrar_vigentes(_artigos(pares, perfil), perfil, relatorio), relatorio.entradas


def _ids(no):
    return [filho.id for filho in no.filhos]


def test_h16_inciso_vi_sai_com_a_rubrica_feminicidio(cp):
    [art], [descarte] = _filtrar(ART_121_P2, cp)
    # Os ids e as penas restantes não são renumerados.
    assert _ids(art.filhos[0]) == [
        "art121.p2.i1",
        "art121.p2.pena1",
        "art121.p2.i7",
        "art121.p2.pena2",
    ]
    assert (descarte.id, descarte.rotulo, descarte.rubrica, descarte.motivo, descarte.origem) == (
        "art121.p2.i6",
        "VI",
        "Feminicídio",
        "revogado",
        "html:p#588",
    )
    assert descarte.texto == (
        "VI (Incluído pela Lei nº 13.104, de 2015) (Revogado pela Lei nº 14.994, de 2024)"
    )
    assert [n.tipo for n in descarte.notas] == ["inclusao", "revogacao"]


def test_h15_art88_revogado_o_livramento_e_vigente(cp):
    pares = [
        (
            407,
            "Art. 88 - Revogado o livramento, não poderá ser novamente concedido, e, salvo "
            "quando a revogação resulta de condenação por outro crime anterior àquele benefício, "
            "não se desconta na pena o tempo em que esteve solto o condenado. (Redação dada pela "
            "Lei nº 7.209, de 11.7.1984)",
        )
    ]
    artigos = _artigos(pares, cp)
    vigentes, entradas = _filtrar(pares, cp)
    assert (vigentes, entradas) == (artigos, ())


def test_rf14_art171_p5_sai_em_cascata_com_os_quatro_incisos(cp):
    [art], descartes = _filtrar(ART_171_P5, cp)
    assert art.filhos == ()
    assert [(d.id, d.rotulo, d.motivo) for d in descartes] == [
        ("art171.p5", "§ 5º", "revogado"),
        ("art171.p5.i1", "I", "revogado"),
        ("art171.p5.i2", "II", "revogado"),
        ("art171.p5.i3", "III", "revogado"),
        ("art171.p5.i4", "IV", "revogado"),
    ]  # pré-ordem
    assert descartes[0].texto == "§ 5º (Revogado) (Redação dada pela Lei nº 15.397, de 2026)"
    assert [d.origem for d in descartes] == [f"html:p#{p}" for p in range(1170, 1175)]


def test_p12_revogado_sem_parenteses_sai_no_perfil_padrao():
    # Lei 11.608/2003 (PDF), arts. 10 e 11 (A11): a revogação vem no texto, sem nota.
    padrao = carregar_perfil("padrao")
    vigentes, [descarte] = _filtrar([(1, "Artigo 10 - Revogado.")], padrao)
    assert vigentes == ()
    assert (descarte.id, descarte.motivo, descarte.notas) == ("art10", "revogado", ())
    assert descarte.texto == f"{descarte.rotulo} Revogado."


def test_p12_revogado_com_ponto_e_nota_sai(cp):
    pares = [
        (1146, ART_171_P5[0][1]),
        (2, "I – Revogado. (Revogado pelo Provimento CG Nº 03/2026)"),
    ]
    [art], [descarte] = _filtrar(pares, cp)
    assert (art.filhos, descarte.id, descarte.motivo) == ((), "art171.i1", "revogado")


def test_rf14_vetado_com_rotulo_sai_com_motivo_vetado(cp):
    pares = [(2368, "Art. 359-O. (VETADO). (Incluído pela Lei nº 14.197, de 2021) (Vigência)")]
    vigentes, [descarte] = _filtrar(pares, cp)
    assert vigentes == ()
    assert (descarte.id, descarte.rotulo, descarte.motivo) == ("art359-O", "Art. 359-O", "vetado")
    assert [n.tipo for n in descarte.notas] == ["veto", "inclusao", "vigencia"]


def test_adr001_no_vazio_com_filho_vigente_fica(cp):
    # O § 5º revogado do art. 171 com um inciso vigente (o I do art. 121, § 2º): fica para a V5.
    pares = [
        ART_171_P5[0],
        ART_171_P5[1],
        (581, "I - mediante paga ou promessa de recompensa, ou por outro motivo torpe;"),
    ]
    [art], entradas = _filtrar(pares, cp)
    assert entradas == ()
    assert art == _artigos(pares, cp)[0]


def test_rf14_pena_vazia_nunca_sai(cp):
    pena = No(id="art1.pena1", tipo="pena", texto="", origem="html:p#2")
    artigo = No(id="art1", tipo="artigo", texto="", origem="html:p#1", filhos=(pena,))
    relatorio = Relatorio()
    assert filtrar_vigentes((artigo,), cp, relatorio) == (artigo,)
    assert relatorio.entradas == ()


def test_rf16_vazio_sem_nota_de_revogacao_nem_veto(cp):
    nota_so_de_redacao = [ART_171_P5[0], (1170, "§ 5º (Redação dada pela Lei nº 15.397, de 2026)")]
    _, [descarte] = _filtrar(nota_so_de_redacao, cp)
    assert descarte.motivo == "vazio"


def test_rf16_veto_e_revogacao_vale_a_primeira_nota(cp):
    pares = [(2368, "Art. 359-O. (Revogado) (VETADO)")]
    _, [descarte] = _filtrar(pares, cp)
    assert descarte.motivo == "revogado"
