import pytest

from vademecum.modelo import LinhaFonte, Nota, Relatorio
from vademecum.normalizador import normalizar
from vademecum.parser import analisar
from vademecum.perfil import carregar_perfil

# Linhas reais do CP (`dados/cp/del2848compilado.mht`), com o `p#` da fonte. As rubricas e os
# níveis entre elas ficam de fora: são reconhecidos em outra etapa do parser (H6, H5).
ART_121 = [
    (575, "Art. 121. Matar alguem:"),
    (576, "Pena - reclusão, de seis a vinte anos."),
    (
        578,
        "§ 1º Se o agente comete o crime impelido por motivo de relevante valor social ou moral, "
        "ou sob o domínio de violenta emoção, logo em seguida a injusta provocação da vítima, o "
        "juiz pode reduzir a pena de um sexto a um terço.",
    ),
    (580, "§ 2º Se o homicídio é cometido:"),
    (581, "I - mediante paga ou promessa de recompensa, ou por outro motivo torpe;"),
    (582, "II - por motivo futil;"),
    (
        583,
        "III - com emprego de veneno, fogo, explosivo, asfixia, tortura ou outro meio insidioso ou "
        "cruel, ou de que possa resultar perigo comum;",
    ),
    (
        584,
        "IV - à traição, de emboscada, ou mediante dissimulação ou outro recurso que dificulte ou "
        "torne impossivel a defesa do ofendido;",
    ),
    (
        585,
        "V - para assegurar a execução, a ocultação, a impunidade ou vantagem de outro crime:",
    ),
    (586, "Pena - reclusão, de doze a trinta anos."),
    (588, "VI - (Revogado pela Lei nº 14.994, de 2024)"),
    (589, "VII – contra: (Redação dada pela Lei nº 15.134, de 2025)"),
    (
        590,
        "a) autoridade ou agente descrito nos arts. 142 e 144 da Constituição Federal, integrantes "
        "do sistema prisional e da Força Nacional de Segurança Pública, no exercício da função ou "
        "em decorrência dela, ou contra seu cônjuge, companheiro ou parente consanguíneo até o "
        "terceiro grau, em razão dessa condição; (Incluída pela Lei nº 15.134, de 2025)",
    ),
    (
        591,
        "b) membro do Poder Judiciário, do Ministério Público, da Defensoria Pública ou da "
        "Advocacia Pública, de que tratam os arts. 131 e 132 da Constituição Federal, ou oficial "
        "de justiça, no exercício da função ou em decorrência dela, ou contra seu cônjuge, "
        "companheiro ou parente, inclusive por afinidade, até o terceiro grau, em razão dessa "
        "condição; (Incluída pela Lei nº 15.134, de 2025)",
    ),
    (
        592,
        "VIII - com emprego de arma de fogo de uso restrito ou proibido: (Incluído pela Lei nº "
        "13.964, de 2019) (Vigência)",
    ),
    (
        594,
        "IX - contra menor de 14 (quatorze) anos: (Incluído pela Lei nº 14.344, de 2022) Vigência",
    ),
    (
        595,
        "X - nas dependências de instituição de ensino: (Incluído pela Lei nº 15.159, de 2025)",
    ),
    (596, "Pena - reclusão, de doze a trinta anos."),
    (597, "§ 2o-A (Revogado pela Lei nº 14.994, de 2024)"),
    (
        598,
        "§ 2º-B. A pena do homicídio contra menor de 14 (quatorze) anos é aumentada de: (Incluído "
        "pela Lei nº 14.344, de 2022) Vigência",
    ),
    (
        605,
        "§ 2º-D. Se o homicídio doloso é cometido por integrante de organização criminosa "
        "ultraviolenta, grupo paramilitar ou milícia privada, no contexto da atuação ou para a "
        "consecução das condutas previstas no art. 2º da lei que institui o marco legal do combate "
        "ao crime organizado no Brasil. (Incluído pela Lei nº 15.358, de 2026)",
    ),
    (
        606,
        "Pena - reclusão, de 20 (vinte) a 40 (quarenta anos). (Incluído pela Lei nº 15.358, de "
        "2026)",
    ),
]


@pytest.fixture(scope="module")
def cp():
    return carregar_perfil("cp")


def _linhas(pares, perfil):
    brutas = [
        LinhaFonte(
            texto=texto,
            negrito=False,
            rotulo_negrito=False,
            centralizado=False,
            cor=None,
            origem=f"html:p#{p}",
        )
        for p, texto in pares
    ]
    return normalizar(brutas, perfil.prefixos_artigo)


def _analisar(pares, perfil, relatorio=None):
    return analisar(_linhas(pares, perfil), perfil, relatorio or Relatorio())


def _filho(no, id_):
    return next(filho for filho in no.filhos if filho.id == id_)


def test_rf08_art121_caput_e_paragrafos(cp):
    [art] = _analisar(ART_121, cp)
    assert (art.id, art.tipo, art.rotulo, art.numero, art.sufixo) == (
        "art121",
        "artigo",
        "Art. 121",
        121,
        (),
    )
    assert art.texto == "Matar alguem:"  # literal, sem corrigir a grafia
    assert art.origem == "html:p#575"
    assert [f.id for f in art.filhos] == [
        "art121.pena1",
        "art121.p1",
        "art121.p2",
        "art121.p2-A",
        "art121.p2-B",
        "art121.p2-D",
    ]
    assert _filho(art, "art121.pena1").texto == "reclusão, de seis a vinte anos."
    assert _filho(art, "art121.p2-B").rotulo == "§ 2º-B"


def test_h14_art121_p2_incisos_com_duas_penas_posicionais(cp):
    [art] = _analisar(ART_121, cp)
    p2 = _filho(art, "art121.p2")
    assert (p2.rotulo, p2.texto) == ("§ 2º", "Se o homicídio é cometido:")
    assert [f.id for f in p2.filhos] == [
        "art121.p2.i1",
        "art121.p2.i2",
        "art121.p2.i3",
        "art121.p2.i4",
        "art121.p2.i5",
        "art121.p2.pena1",
        "art121.p2.i6",
        "art121.p2.i7",
        "art121.p2.i8",
        "art121.p2.i9",
        "art121.p2.i10",
        "art121.p2.pena2",
    ]
    assert {f.tipo for f in p2.filhos} == {"inciso", "pena"}
    assert _filho(p2, "art121.p2.pena2").texto == "reclusão, de doze a trinta anos."


def test_rf08_inciso_vii_com_alineas_e_notas(cp):
    [art] = _analisar(ART_121, cp)
    vii = _filho(_filho(art, "art121.p2"), "art121.p2.i7")
    assert (vii.rotulo, vii.texto) == ("VII", "contra:")
    assert vii.notas == (
        Nota(
            tipo="redacao",
            bruto="(Redação dada pela Lei nº 15.134, de 2025)",
            norma="Lei nº 15.134",
            ano=2025,
        ),
    )
    assert [(f.id, f.tipo, f.rotulo) for f in vii.filhos] == [
        ("art121.p2.i7.a", "alinea", "a"),
        ("art121.p2.i7.b", "alinea", "b"),
    ]
    assert vii.filhos[0].texto.startswith("autoridade ou agente descrito")
    assert vii.filhos[0].texto.endswith("em razão dessa condição;")
    assert [n.tipo for n in vii.filhos[0].notas] == ["inclusao"]


def test_rf12_texto_sem_nota_e_dispositivo_so_de_nota(cp):
    [art] = _analisar(ART_121, cp)
    p2 = _filho(art, "art121.p2")
    ix = _filho(p2, "art121.p2.i9")
    assert ix.texto == "contra menor de 14 (quatorze) anos:"
    assert [n.tipo for n in ix.notas] == ["inclusao", "vigencia"]
    # Revogado fica na árvore com texto vazio; o filtro de vigência é de outra etapa (ADR-001).
    vi = _filho(p2, "art121.p2.i6")
    assert (vi.texto, [n.tipo for n in vi.notas]) == ("", ["revogacao"])
    assert _filho(art, "art121.p2-A").texto == ""


def test_a3_paragrafo_2d_com_pena_propria(cp):
    [art] = _analisar(ART_121, cp)
    p2d = _filho(art, "art121.p2-D")
    assert p2d.rotulo == "§ 2º-D"
    [pena] = p2d.filhos
    assert (pena.id, pena.tipo) == ("art121.p2-D.pena1", "pena")
    assert pena.texto == "reclusão, de 20 (vinte) a 40 (quarenta anos)."
    assert [n.bruto for n in pena.notas] == ["(Incluído pela Lei nº 15.358, de 2026)"]


def test_rf08_inciso_sem_hifen_antes_de_minuscula(cp):
    # CP, art. 129, § 2º: a fonte traz `III perda…` sem hífen (`p#684`).
    pares = [
        (668, "Art. 129. Ofender a integridade corporal ou a saúde de outrem:"),
        (681, "§ 2° Se resulta:"),
        (682, "I - Incapacidade permanente para o trabalho;"),
        (683, "II - enfermidade incuravel;"),
        (684, "III perda ou inutilização do membro, sentido ou função;"),
        (685, "IV - deformidade permanente;"),
    ]
    [art] = _analisar(pares, cp)
    p2 = _filho(art, "art129.p2")
    assert [(f.rotulo, f.texto) for f in p2.filhos] == [
        ("I", "Incapacidade permanente para o trabalho;"),
        ("II", "enfermidade incuravel;"),
        ("III", "perda ou inutilização do membro, sentido ou função;"),
        ("IV", "deformidade permanente;"),
    ]
    assert p2.rotulo == "§ 2º"  # A8


def test_rf09_pena_com_dois_pontos(cp):
    # CP, art. 319-A (`p#2032`): `Pena:` em vez de `Pena -`.
    pares = [
        (
            2031,
            "Art. 319-A. Deixar o Diretor de Penitenciária e/ou agente público, de cumprir seu "
            "dever de vedar ao preso o acesso a aparelho telefônico, de rádio ou similar, que "
            "permita a comunicação com outros presos ou com o ambiente externo: (Incluído pela Lei "
            "nº 11.466, de 2007).",
        ),
        (2032, "Pena: detenção, de 3 (três) meses a 1 (um) ano."),
    ]
    [art] = _analisar(pares, cp)
    assert (art.id, art.sufixo) == ("art319-A", ("A",))
    assert [(f.id, f.texto) for f in art.filhos] == [
        ("art319-A.pena1", "detenção, de 3 (três) meses a 1 (um) ano.")
    ]


def test_rf09_pena_de_multa_nao_e_pena(cp):
    # `Pena de multa` (`p#272`) é rubrica: sem separador, não abre pena.
    pares = [(270, "Art. 48 - A limitação de fim de semana consiste…"), (272, "Pena de multa")]
    [art] = _analisar(pares, cp)
    assert art.filhos == ()


def test_a7_paragrafo_unico(cp):
    # CP, art. 2º (`p#25`, `p#26`).
    pares = [
        (
            25,
            "Art. 2º - Ninguém pode ser punido por fato que lei posterior deixa de considerar "
            "crime. (Redação dada pela Lei nº 7.209, de 11.7.1984)",
        ),
        (
            26,
            "Parágrafo único - A lei posterior, que de qualquer modo favorecer o agente, aplica-se "
            "aos fatos anteriores. (Redação dada pela Lei nº 7.209, de 11.7.1984)",
        ),
    ]
    [art] = _analisar(pares, cp)
    assert (art.rotulo, art.id) == ("Art. 2º", "art2")
    [pu] = art.filhos
    assert (pu.id, pu.tipo, pu.rotulo) == ("art2.pu", "paragrafo", "Parágrafo único")
    assert pu.texto.startswith("A lei posterior")


def test_rf08_alinea_do_paragrafo_depois_de_inciso_do_caput(cp):
    # CP, art. 7º: o § 2º fecha o inciso II do caput; as alíneas seguintes são do § 2º.
    pares = [
        (38, "Art. 7º - Ficam sujeitos à lei brasileira, embora cometidos no estrangeiro:"),
        (44, "II - os crimes: (Redação dada pela Lei nº 7.209, de 11.7.1984)"),
        (46, "b) praticados por brasileiro; (Incluído pela Lei nº 7.209, de 1984)"),
        (
            49,
            "§ 2º - Nos casos do inciso II, a aplicação da lei brasileira depende do concurso das "
            "seguintes condições: (Incluído pela Lei nº 7.209, de 1984)",
        ),
        (50, "a) entrar o agente no território nacional; (Incluído pela Lei nº 7.209, de 1984)"),
    ]
    [art] = _analisar(pares, cp)
    assert [f.id for f in art.filhos] == ["art7.i2", "art7.p2"]
    assert [f.id for f in art.filhos[0].filhos] == ["art7.i2.b"]
    assert [f.id for f in art.filhos[1].filhos] == ["art7.p2.a"]


def test_h12_artigo_com_sufixo_composto(cp):
    # CP, art. 359-M-A (`p#2359`), A6.
    pares = [(2359, "Art. 359-M-A. Quando os delitos deste Capítulo estão inseridos…")]
    [art] = _analisar(pares, cp)
    assert (art.id, art.rotulo, art.numero, art.sufixo) == (
        "art359-M-A",
        "Art. 359-M-A",
        359,
        ("M", "A"),
    )


def test_rf11_continuacao_e_linha_so_de_nota_vao_ao_corrente(cp):
    pares = [
        (575, "Art. 121. Matar alguem:"),
        (576, "Pena - reclusão,"),
        (577, "de seis a vinte anos."),
        (578, "(Vide Lei nº 4.611, de 1965)"),
    ]
    [art] = _analisar(pares, cp)
    [pena] = art.filhos
    assert pena.texto == "reclusão, de seis a vinte anos."
    assert [n.tipo for n in pena.notas] == ["remissao"]
    assert art.notas == ()


def test_v7_linha_antes_do_primeiro_artigo_vai_ao_relatorio(cp):
    relatorio = Relatorio()
    pares = [(6, "(Vide Lei nº 1.521, de 1951)"), (7, "I - solto"), (23, "Art. 1º - Não há crime.")]
    [art] = _analisar(pares, cp, relatorio)
    assert art.id == "art1"
    assert [(e.tipo, e.origem, e.texto) for e in relatorio.entradas] == [
        ("nao_classificada", "html:p#6", "(Vide Lei nº 1.521, de 1951)"),
        ("nao_classificada", "html:p#7", "I - solto"),
    ]


def test_p9_prefixo_de_artigo_vem_do_perfil():
    # Lei estadual: `Artigo 1° -` (P9), aceito pelo `padrao`.
    padrao = carregar_perfil("padrao")
    [art] = _analisar([(1, "Artigo 1° - Esta lei dispõe…")], padrao)
    assert (art.id, art.rotulo, art.texto) == ("art1", "Artigo 1º", "Esta lei dispõe…")
