import pytest

from vademecum.modelo import LinhaFonte, Local, Nota, Relatorio
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
    """`(p, texto)` ou `(p, texto, marca)`; `marca` é `"negrito"`, `"rotulo"` ou `"centro"`."""
    brutas = [
        LinhaFonte(
            texto=par[1],
            negrito="negrito" in par[2:],
            rotulo_negrito="rotulo" in par[2:],
            centralizado="centro" in par[2:],
            cor=None,
            origem=f"html:p#{par[0]}",
        )
        for par in pares
    ]
    return normalizar(brutas, perfil.prefixos_artigo)


def _analise(pares, perfil, relatorio=None):
    return analisar(_linhas(pares, perfil), perfil, relatorio or Relatorio())


def _analisar(pares, perfil, relatorio=None):
    return _analise(pares, perfil, relatorio).artigos


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


def test_v7_linha_sem_dispositivo_aberto_vai_ao_relatorio(cp):
    # Depois do nível não há dispositivo corrente; o inciso sem artigo não tem pai.
    relatorio = Relatorio()
    pares = [
        (19, "TÍTULO I", "negrito", "centro"),
        (20, "DA APLICAÇÃO DA LEI PENAL", "negrito", "centro"),
        (7, "I - solto"),
        (23, "Art. 1º - Não há crime."),
    ]
    [art] = _analisar(pares, cp, relatorio)
    assert art.id == "art1"
    assert [(e.tipo, e.origem, e.texto) for e in relatorio.entradas] == [
        ("nao_classificada", "html:p#7", "I - solto"),
    ]


def test_p9_prefixo_de_artigo_vem_do_perfil():
    # Lei estadual: `Artigo 1° -` (P9), aceito pelo `padrao`.
    padrao = carregar_perfil("padrao")
    [art] = _analisar([(1, "Artigo 1° - Esta lei dispõe…")], padrao)
    assert (art.id, art.rotulo, art.texto) == ("art1", "Artigo 1º", "Esta lei dispõe…")


def test_h6a_rubrica_em_negrito_liga_ao_artigo_e_ao_paragrafo(cp):
    # CP, art. 121 (`p#572`–`p#579`); sem o nível antes, a rubrica seria cabeçalho (H17).
    pares = [
        (572, "CAPÍTULO I", "negrito", "centro"),
        (573, "DOS CRIMES CONTRA A VIDA", "negrito", "centro"),
        (574, "Homicídio simples", "negrito"),
        (575, "Art. 121. Matar alguem:"),
        (576, "Pena - reclusão, de seis a vinte anos."),
        (579, "Homicídio qualificado", "negrito"),
        (580, "§ 2º Se o homicídio é cometido:"),
    ]
    [art] = _analisar(pares, cp)
    assert (art.rubrica, art.texto) == ("Homicídio simples", "Matar alguem:")
    assert _filho(art, "art121.p2").rubrica == "Homicídio qualificado"
    assert _filho(art, "art121.pena1").texto == "reclusão, de seis a vinte anos."


def test_h6b_h7_rubrica_com_nota_fora_do_negrito(cp):
    # CP, art. 6º (`p#35`): só `Lugar do crime` está no `<b>`.
    pares = [
        (34, "Art. 5º - Aplica-se a lei brasileira…"),
        (35, "Lugar do crime (Redação dada pela Lei nº 7.209, de 1984)", "rotulo"),
        (
            36,
            "Art. 6º - Considera-se praticado o crime no lugar em que ocorreu a ação ou omissão, "
            "no todo ou em parte, bem como onde se produziu ou deveria produzir-se o "
            "resultado.(Redação dada pela Lei nº 7.209, de 1984)",
        ),
    ]
    art5, art6 = _analisar(pares, cp)
    assert art5.texto == "Aplica-se a lei brasileira…"
    assert art6.rubrica == "Lugar do crime"
    assert art6.texto.endswith("deveria produzir-se o resultado.")
    # H7: a nota da rubrica vem antes da nota do próprio artigo.
    assert [n.bruto for n in art6.notas] == [
        "(Redação dada pela Lei nº 7.209, de 1984)",
        "(Redação dada pela Lei nº 7.209, de 1984)",
    ]


def test_h6b_inicio_em_negrito_sem_dispositivo_seguinte_nao_e_rubrica(cp):
    # Caso montado: a linha de `p#35` seguida de nível, e não do art. 6º, é continuação (RF11).
    pares = [
        (34, "Art. 5º - Aplica-se a lei brasileira…"),
        (35, "Lugar do crime (Redação dada pela Lei nº 7.209, de 1984)", "rotulo"),
        (570, "TÍTULO I", "negrito", "centro"),
    ]
    [art5] = _analisar(pares, cp)
    assert art5.rubrica is None
    assert art5.texto == "Aplica-se a lei brasileira… Lugar do crime"


def test_h6c_rubrica_sem_negrito_com_nota(cp):
    # CP: `Feminicídio` (`p#615`) e `Sabotagem` (`p#2378`) vêm sem negrito nenhum.
    pares = [
        (614, "§ 7º (Revogado pela Lei nº 14.994, de 2024)"),
        (615, "Feminicídio (Incluído pela Lei nº 14.994, de 2024)"),
        (
            616,
            "Art. 121-A. Matar mulher por razões da condição do sexo feminino: (Incluído pela Lei "
            "nº 14.994, de 2024)",
        ),
        (2378, "Sabotagem (Incluído pela Lei nº 14.197, de 2021) (Vigência)"),
        (
            2379,
            "Art. 359-R. Destruir ou inutilizar meios de comunicação ao público… (Incluído pela "
            "Lei nº 14.197, de 2021) (Vigência)",
        ),
    ]
    art121a, art359r = _analisar([(575, "Art. 121. Matar alguem:"), *pares], cp)[1:]
    assert (art121a.id, art121a.rubrica) == ("art121-A", "Feminicídio")
    assert [n.bruto for n in art121a.notas] == [
        "(Incluído pela Lei nº 14.994, de 2024)",
        "(Incluído pela Lei nº 14.994, de 2024)",
    ]
    assert (art359r.id, art359r.rubrica) == ("art359-R", "Sabotagem")
    assert [n.tipo for n in art359r.notas] == ["inclusao", "vigencia", "inclusao", "vigencia"]


def test_h6c_rubrica_sem_negrito_antes_de_inciso(cp):
    # CP, art. 121, § 2º (`p#593`): a rubrica do IX, com `Vigência` sem parênteses.
    pares = [
        (580, "§ 2º Se o homicídio é cometido:"),
        (
            593,
            "Homicídio contra menor de 14 (quatorze) anos (Incluído pela Lei nº 14.344, de 2022) "
            "Vigência",
        ),
        (
            594,
            "IX - contra menor de 14 (quatorze) anos: (Incluído pela Lei nº 14.344, de 2022) "
            "Vigência",
        ),
    ]
    [art] = _analisar([(575, "Art. 121. Matar alguem:"), *pares], cp)
    ix = _filho(_filho(art, "art121.p2"), "art121.p2.i9")
    assert ix.rubrica == "Homicídio contra menor de 14 (quatorze) anos"
    assert ix.texto == "contra menor de 14 (quatorze) anos:"


def test_h6c_linha_pontuada_ou_pena_nao_e_rubrica(cp):
    # `III perda…;` (`p#684`) termina em `;`: é inciso, não rubrica do IV. `Pena - … anos (…)`
    # (`p#1380`) não termina em ponto, mas tem padrão de pena.
    pares = [
        (668, "Art. 129. Ofender a integridade corporal ou a saúde de outrem:"),
        (681, "§ 2º Se resulta:"),
        (684, "III perda ou inutilização do membro, sentido ou função;"),
        (685, "IV - deformidade permanente;"),
        (1379, "Art. 213. Constranger alguém…"),
        (
            1380,
            "Pena - reclusão, de 12 (doze) a 30 (trinta) anos (Incluído pela Lei nº 12.015, de "
            "2009)",
        ),
        (1381, "Art. 214 - (Revogado pela Lei nº 12.015, de 2009)"),
    ]
    art129, art213, _ = _analisar(pares, cp)
    assert [(f.rotulo, f.rubrica) for f in _filho(art129, "art129.p2").filhos] == [
        ("III", None),
        ("IV", None),
    ]
    assert [f.tipo for f in art213.filhos] == ["pena"]


def test_h6c_rubrica_sem_negrito_desligada_no_padrao():
    padrao = carregar_perfil("padrao")
    pares = [(575, "Art. 121. Matar alguem:"), (2378, "Sabotagem"), (2379, "Art. 359-R. Destruir…")]
    art121, art359r = _analisar(pares, padrao)
    assert art359r.rubrica is None
    assert art121.texto == "Matar alguem: Sabotagem"  # RF11: continuação


def test_h7_rubrica_sem_dispositivo_seguinte_vira_aviso(cp):
    relatorio = Relatorio()
    pares = [
        (575, "Art. 121. Matar alguem:"),
        (576, "Pena - reclusão, de seis a vinte anos."),
        (577, "Caso de diminuição de pena", "negrito"),
    ]
    [art] = _analisar(pares, cp, relatorio)
    assert [(e.tipo, e.origem, e.texto) for e in relatorio.entradas] == [
        ("aviso", "html:p#577", "Caso de diminuição de pena")
    ]
    assert _filho(art, "art121.pena1").texto == "reclusão, de seis a vinte anos."


def test_rf11_vetado_sem_rotulo_e_descarte(cp):
    # CP, art. 359-N (`p#2367`) e art. 359-T (`p#2388`): a linha não é nota do dispositivo anterior.
    relatorio = Relatorio()
    vetado = "(VETADO) (Incluído pela Lei nº 14.197, de 2021) (Vigência)"
    pares = [
        (
            2365,
            "Art. 359-N. Impedir ou perturbar a eleição… (Incluído pela Lei nº 14.197, de 2021)",
        ),
        (2366, "Pena - reclusão, de 3 (três) a 6 (seis) anos, e multa."),
        (2367, vetado),
        (2368, "Art. 359-O. (VETADO). (Incluído pela Lei nº 14.197, de 2021) (Vigência)"),
        (2387, "Art. 359-T. Não constitui crime previsto neste Título a manifestação crítica…"),
        (2388, vetado),
    ]
    art359n, art359o, art359t = _analisar(pares, cp, relatorio)
    assert [(e.tipo, e.origem, e.texto) for e in relatorio.entradas] == [
        ("descarte", "html:p#2367", vetado),
        ("descarte", "html:p#2388", vetado),
    ]
    assert art359n.filhos[0].notas == ()
    assert art359t.notas == ()
    # Com rótulo, o `(VETADO)` é nota do próprio artigo (o filtro de vigência é de outra etapa).
    assert (art359o.texto, [n.tipo for n in art359o.notas]) == (
        "",
        ["veto", "inclusao", "vigencia"],
    )


def test_h5_h18_art121_local_e_nota_de_nivel(cp):
    # CP, `p#567`–`p#575`: a nota da PARTE ESPECIAL não tem nó e vira `aviso`.
    relatorio = Relatorio()
    pares = [
        (567, "Art. 120 - A sentença que conceder perdão judicial não será considerada…"),
        (568, "PARTE ESPECIAL", "negrito", "centro"),
        (569, "(Vide Lei nº 7.209, de 1984)", "centro"),
        (570, "TÍTULO I", "negrito", "centro"),
        (571, "DOS CRIMES CONTRA A PESSOA", "negrito", "centro"),
        (572, "CAPÍTULO I", "negrito", "centro"),
        (573, "DOS CRIMES CONTRA A VIDA", "negrito", "centro"),
        (574, "Homicídio simples", "negrito"),
        (575, "Art. 121. Matar alguem:"),
    ]
    art120, art121 = _analisar(pares, cp, relatorio)
    assert art120.local == Local()  # P8: hierarquia ausente
    assert art120.texto.endswith("considerada…")
    assert art121.local == Local(
        parte="PARTE ESPECIAL",
        titulo="TÍTULO I — DOS CRIMES CONTRA A PESSOA",
        capitulo="CAPÍTULO I — DOS CRIMES CONTRA A VIDA",
    )
    assert art121.rubrica == "Homicídio simples"
    assert [(e.tipo, e.origem) for e in relatorio.entradas] == [("aviso", "html:p#569")]


def test_h5_nome_em_duas_linhas(cp):
    # CP, Seção III do Capítulo VI do Título I (`p#918`–`p#922`).
    pares = [
        (570, "TÍTULO I", "negrito", "centro"),
        (571, "DOS CRIMES CONTRA A PESSOA", "negrito", "centro"),
        (918, "SEÇÃO III", "negrito", "centro"),
        (919, "DOS CRIMES CONTRA A", "negrito", "centro"),
        (920, "INVIOLABILIDADE DE CORRESPONDÊNCIA", "negrito", "centro"),
        (921, "Violação de correspondência", "negrito"),
        (922, "Art. 151 - Devassar indevidamente o conteúdo de correspondência fechada…"),
    ]
    [art] = _analisar(pares, cp)
    assert art.local == Local(
        titulo="TÍTULO I — DOS CRIMES CONTRA A PESSOA",
        secao="SEÇÃO III — DOS CRIMES CONTRA A INVIOLABILIDADE DE CORRESPONDÊNCIA",
    )
    assert art.rubrica == "Violação de correspondência"


def test_h5_nivel_sem_negrito_nota_antes_do_nome_e_nivel_novo_zera_os_de_baixo(cp):
    # CP, Título XII: `CAPÍTULO IV` sem negrito, com a nota antes do nome (`p#2374`–`p#2379`).
    relatorio = Relatorio()
    pares = [
        (2329, "CAPÍTULO I", "negrito", "centro"),
        (2331, "DOS CRIMES CONTRA A SOBERANIA NACIONAL", "negrito", "centro"),
        (2373, "Art. 359-Q. (VETADO). (Incluído pela Lei nº 14.197, de 2021) (Vigência)"),
        (2374, "CAPÍTULO IV", "centro"),
        (2375, "(Incluído pela Lei nº 14.197, de 2021) (Vigência)", "centro"),
        (2376, "DOS CRIMES CONTRA O FUNCIONAMENTO", "centro"),
        (2377, "DOS SERVIÇOS ESSENCIAIS", "centro"),
        (2378, "Sabotagem (Incluído pela Lei nº 14.197, de 2021) (Vigência)"),
        (2379, "Art. 359-R. Destruir ou inutilizar meios de comunicação ao público…"),
        (9000, "TÍTULO XIII", "negrito", "centro"),
        (9001, "Art. 999 - Linha inventada para o teste: o título novo fecha o capítulo."),
    ]
    art359q, art359r, art999 = _analisar(pares, cp, relatorio)
    assert art359q.local == Local(capitulo="CAPÍTULO I — DOS CRIMES CONTRA A SOBERANIA NACIONAL")
    assert art359r.local == Local(
        capitulo="CAPÍTULO IV — DOS CRIMES CONTRA O FUNCIONAMENTO DOS SERVIÇOS ESSENCIAIS"
    )
    assert art359r.rubrica == "Sabotagem"
    assert art999.local == Local(titulo="TÍTULO XIII")
    assert [(e.tipo, e.origem) for e in relatorio.entradas] == [("aviso", "html:p#2375")]


def test_h6d_rubrica_centralizada_em_caixa_mista_nao_e_nome(cp):
    # CP, Capítulo I-A do Título VI (`p#1395`–`p#1399`).
    pares = [
        (1395, "CAPÍTULO I-A", "negrito", "centro"),
        (1396, "(Incluído pela Lei nº 13.772, de 2018)", "centro"),
        (1397, "DA EXPOSIÇÃO DA INTIMIDADE SEXUAL", "negrito", "centro"),
        (1398, "Registro não autorizado da intimidade sexual", "negrito", "centro"),
        (1399, "Art. 216-B. Produzir, fotografar, filmar ou registrar, por qualquer meio…"),
    ]
    [art] = _analisar(pares, cp)
    assert art.local == Local(capitulo="CAPÍTULO I-A — DA EXPOSIÇÃO DA INTIMIDADE SEXUAL")
    assert art.rubrica == "Registro não autorizado da intimidade sexual"


def test_h5_nome_todo_em_minusculas_continua_nome(cp):
    # CP, Capítulo V do Título X (`p#1966`–`p#1971`): o nome vem em minúsculas, entre notas.
    pares = [
        (1966, "CAPÍTULO V", "negrito", "centro"),
        (1967, "(Incluído pela Lei 12.550. de 2011)", "centro"),
        (1968, "das fraudes em certames de interesse público", "negrito", "centro"),
        (1969, "(Incluído pela Lei 12.550. de 2011)", "centro"),
        (
            1970,
            "Fraudes em certames de interesse público (Incluído pela Lei 12.550. de 2011)",
            "rotulo",
        ),
        (1971, "Art. 311-A. Utilizar ou divulgar, indevidamente, com o fim de beneficiar a si…"),
    ]
    [art] = _analisar(pares, cp)
    assert art.local == Local(capitulo="CAPÍTULO V — das fraudes em certames de interesse público")
    assert art.rubrica == "Fraudes em certames de interesse público"


def test_p8_rotulo_livre_fecha_os_niveis_abaixo_da_parte(cp):
    # CP, `p#2381`–`p#2391`; o `(VETADO)` solto depois do nível também é descarte (RF11).
    relatorio = Relatorio()
    vetado = "(VETADO) (Incluído pela Lei nº 14.197, de 2021) (Vigência)"
    pares = [
        (568, "PARTE ESPECIAL", "negrito", "centro"),
        (2325, "TÍTULO XII", "negrito", "centro"),
        (2327, "DOS CRIMES CONTRA O ESTADO", "negrito", "centro"),
        (2328, "DEMOCRÁTICO DE DIREITO", "centro"),
        (2381, "CAPÍTULO V", "centro"),
        (2383, vetado),
        (2384, "CAPÍTULO VI", "centro"),
        (2386, "DISPOSIÇÕES COMUNS", "centro"),
        (2387, "Art. 359-T. Não constitui crime previsto neste Título a manifestação crítica…"),
        (2390, "DISPOSIÇÕES FINAIS", "negrito", "centro"),
        (2391, "Art. 360 - Ressalvada a legislação especial sobre os crimes contra a existência…"),
    ]
    art359t, art360 = _analisar(pares, cp, relatorio)
    assert art359t.local == Local(
        parte="PARTE ESPECIAL",
        titulo="TÍTULO XII — DOS CRIMES CONTRA O ESTADO DEMOCRÁTICO DE DIREITO",
        capitulo="CAPÍTULO VI — DISPOSIÇÕES COMUNS",
    )
    assert art360.local == Local(parte="PARTE ESPECIAL", rotulo_livre="DISPOSIÇÕES FINAIS")
    assert [(e.tipo, e.origem) for e in relatorio.entradas] == [("descarte", "html:p#2383")]


CABECALHO = [
    (1, "Presidência da República", "negrito", "centro"),
    (2, "Casa Civil", "negrito", "centro"),
    (3, "Subchefia para Assuntos Jurídicos", "negrito", "centro"),
    (4, "DECRETO-LEI No 2.848, DE 7 DE DEZEMBRO DE 1940", "negrito", "centro"),
    (5, "Vigência"),
    (6, "(Vide Lei nº 1.521, de 1951)"),
    (16, "Código Penal."),
    (
        17,
        "O PRESIDENTE DA REPÚBLICA, usando da atribuição que lhe confere o art. 180 da "
        "Constituição, decreta a seguinte lei:",
        "rotulo",
    ),
]


def test_h17_cabecalho_titulo_e_ementa(cp):
    # CP, `p#1`–`p#23`: o cabeçalho vai até o primeiro nível; nada dele é linha não classificada.
    relatorio = Relatorio()
    pares = [
        *CABECALHO,
        (18, "PARTE GERAL", "negrito", "centro"),
        (19, "TÍTULO I", "negrito", "centro"),
        (20, "DA APLICAÇÃO DA LEI PENAL", "negrito", "centro"),
        (21, "(Redação dada pela Lei nº 7.209, de 11.7.1984)", "centro"),
        (22, "Anterioridade da Lei", "negrito"),
        (23, "Art. 1º - Não há crime sem lei anterior que o defina."),
    ]
    analise = _analise(pares, cp, relatorio)
    assert analise.titulo == "DECRETO-LEI No 2.848, DE 7 DE DEZEMBRO DE 1940"
    assert analise.ementa == "Código Penal."
    assert analise.metadados.preambulo == "\n".join(par[1] for par in CABECALHO)
    [art] = analise.artigos
    assert (art.rubrica, art.local.parte) == ("Anterioridade da Lei", "PARTE GERAL")
    assert [(e.tipo, e.origem) for e in relatorio.entradas] == [("aviso", "html:p#21")]


def test_h17_rodape_sai_do_ultimo_artigo(cp):
    # CP, `p#2392`–`p#2397`: o rodapé abre em `Rio de Janeiro, 7 de dezembro de 1940;`.
    rodape = [
        (2393, "Rio de Janeiro, 7 de dezembro de 1940; 119º da Independência e 52º da República."),
        (2394, "GETÚLIO VARGAS"),
        (2395, "Francisco Campos"),
        (
            2396,
            "Este texto não substitui o publicado no DOU de 31.12.1940 e retificado em 3.1.1941",
        ),
        (2397, "*", "centro"),
    ]
    relatorio = Relatorio()
    pares = [
        (2392, "Art. 361 - Este Código entrará em vigor no dia 1º de janeiro de 1942."),
        *rodape,
    ]
    analise = _analise(pares, cp, relatorio)
    [art] = analise.artigos
    assert art.texto == "Este Código entrará em vigor no dia 1º de janeiro de 1942."
    assert analise.metadados.rodape == "\n".join(par[1] for par in rodape)
    assert relatorio.entradas == ()


def test_h17_sem_cabecalho_nem_rodape(cp):
    analise = _analise([(23, "Art. 1º - Não há crime sem lei anterior que o defina.")], cp)
    assert (analise.titulo, analise.ementa) == (None, None)
    assert (analise.metadados.preambulo, analise.metadados.rodape) == (None, None)
    assert [art.id for art in analise.artigos] == ["art1"]
