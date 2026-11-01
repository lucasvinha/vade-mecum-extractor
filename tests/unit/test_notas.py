import pytest

from vademecum.modelo import Nota, Relatorio
from vademecum.notas import extrair_notas
from vademecum.perfil import carregar_perfil


@pytest.fixture(scope="module")
def cp():
    return carregar_perfil("cp")


def _extrair(texto, perfil, relatorio=None):
    return extrair_notas(texto, perfil, "html:p#1", relatorio or Relatorio())


def test_rf12_redacao_com_data_inteira(cp):
    # CP, art. 1º (`p#23`).
    texto, notas = _extrair(
        "Não há crime sem lei anterior que o defina. Não há pena sem prévia cominação legal. "
        "(Redação dada pela Lei nº 7.209, de 11.7.1984)",
        cp,
    )
    assert texto == (
        "Não há crime sem lei anterior que o defina. Não há pena sem prévia cominação legal."
    )
    assert notas == (
        Nota(
            tipo="redacao",
            bruto="(Redação dada pela Lei nº 7.209, de 11.7.1984)",
            norma="Lei nº 7.209",
            ano=1984,
            data="1984-07-11",
        ),
    )


def test_rf12_so_o_ano_deixa_data_nula(cp):
    _, [nota] = _extrair("contra: (Redação dada pela Lei nº 15.134, de 2025)", cp)
    assert (nota.norma, nota.ano, nota.data) == ("Lei nº 15.134", 2025, None)


def test_h10_vigencia_entre_parenteses_e_mais_de_uma_nota(cp):
    # CP, art. 359-P (`p#2370`).
    texto, notas = _extrair(
        "a qualquer pessoa em razão de seu sexo: (Incluído pela Lei nº 14.197, de 2021) (Vigência)",
        cp,
    )
    assert texto == "a qualquer pessoa em razão de seu sexo:"
    assert [(n.tipo, n.bruto) for n in notas] == [
        ("inclusao", "(Incluído pela Lei nº 14.197, de 2021)"),
        ("vigencia", "(Vigência)"),
    ]
    assert (notas[1].norma, notas[1].ano) == (None, None)


def test_h10_vigencia_sem_parenteses_no_fim(cp):
    # CP, art. 129, § 13 (`… de 2022) Vigência`).
    texto, notas = _extrair(
        "Pena - reclusão, de 2 (dois) a 5 (cinco) anos. (Incluído pela Lei nº 14.188, de 2021) "
        "Vigência",
        cp,
    )
    assert texto == "Pena - reclusão, de 2 (dois) a 5 (cinco) anos."
    assert [(n.tipo, n.bruto) for n in notas] == [
        ("inclusao", "(Incluído pela Lei nº 14.188, de 2021)"),
        ("vigencia", "Vigência"),
    ]


def test_h10_vigencia_minuscula_no_meio_e_texto(cp):
    # CP, art. 3º: "durante sua vigência." é texto legal.
    texto, notas = _extrair("aplica-se ao fato praticado durante sua vigência.", cp)
    assert (texto, notas) == ("aplica-se ao fato praticado durante sua vigência.", ())


def test_rf12_inclusao_com_dada_por_engano_na_fonte(cp):
    # CP, art. 154-A (`p#1828`): o Planalto escreveu "Incluído dada".
    _, [nota] = _extrair("(Incluído dada pela Lei nº 12.720, de 2012)", cp)
    assert (nota.tipo, nota.norma, nota.ano) == ("inclusao", "Lei nº 12.720", 2012)


def test_rf12_lei_sem_numero_ordinal_e_com_ponto_antes_do_de(cp):
    # CP, Título X, Capítulo V (`p#1970`).
    _, [nota] = _extrair("(Incluído pela Lei 12.550. de 2011)", cp)
    assert (nota.tipo, nota.norma, nota.ano, nota.data) == ("inclusao", "Lei 12.550", 2011, None)


def test_rf12_data_por_extenso_e_data_incompleta(cp):
    # CPC, art. 63, § 1º; CP, art. 61, II, h (`de 15 de 2001`, sem o mês).
    _, [extenso] = _extrair("(Redação dada pela Lei nº 14.879, de 4 de junho de 2024)", cp)
    assert (extenso.ano, extenso.data) == (2024, "2024-06-04")
    _, [sem_mes] = _extrair("(Incluído pela Lei nº 10.224, de 15 de 2001)", cp)
    assert (sem_mes.ano, sem_mes.data) == (2001, None)


def test_rf12_ordinal_no_dia(cp):
    _, [nota] = _extrair("(Redação dada pela Lei nº 9.677, de 1º.7.1998)", cp)
    assert nota.data == "1998-07-01"


def test_rf12_numero_da_adpf_nao_e_ano(cp):
    _, [nota] = _extrair("(Vide ADPF 1107)", cp)
    assert (nota.tipo, nota.norma, nota.ano) == ("remissao", "ADPF 1107", None)


def test_rf12_parentese_do_texto_legal_fica(cp):
    # `(quatorze)` e `(art. 55)` são texto do CP, não nota.
    texto, notas = _extrair(
        "Se a vítima é menor de 14 (quatorze) anos, em menor tempo (art. 55), a pena", cp
    )
    assert texto == "Se a vítima é menor de 14 (quatorze) anos, em menor tempo (art. 55), a pena"
    assert notas == ()


def test_v6_parentese_com_lei_nao_classificado_vira_nota_outra(cp):
    # CP, art. 153, § 1º (`p#944`).
    relatorio = Relatorio()
    texto, [nota] = extrair_notas(
        "Somente se procede mediante representação. (Parágrafo único renumerado pela Lei nº "
        "9.983, de 2000)",
        cp,
        "html:p#944",
        relatorio,
    )
    assert texto == "Somente se procede mediante representação."
    assert (nota.tipo, nota.norma, nota.ano) == ("outra", "Lei nº 9.983", 2000)
    [entrada] = relatorio.entradas
    assert (entrada.tipo, entrada.origem, entrada.texto) == ("nota_outra", "html:p#944", nota.bruto)


def test_rf12_ponto_depois_da_nota_e_da_nota(cp):
    # CP, art. 109, VI: `ano. (Redação dada…).`; o ponto literal antes da nota fica.
    texto, _ = _extrair(
        "VI - em 3 (três) anos, se o máximo da pena é inferior a 1 (um) ano. (Redação dada pela "
        "Lei nº 12.234, de 2010).",
        cp,
    )
    assert texto == "VI - em 3 (três) anos, se o máximo da pena é inferior a 1 (um) ano."


def test_rf12_nota_colada_ao_ponto(cp):
    # CP, art. 4º: `resultado.(Redação dada…)`.
    texto, _ = _extrair("ainda que outro seja o momento do resultado.(Redação dada pela Lei)", cp)
    assert texto == "ainda que outro seja o momento do resultado."


def test_rf14_vetado_e_so_pontuacao_deixa_texto_vazio(cp):
    # CP, art. 359-Q, depois do rótulo.
    texto, notas = _extrair("(VETADO). (Incluído pela Lei nº 14.197, de 2021) (Vigência)", cp)
    assert texto == ""
    assert [n.tipo for n in notas] == ["veto", "inclusao", "vigencia"]


def test_p16_nr_e_redacao(cp):
    _, [nota] = _extrair("texto. (NR)", cp)
    assert nota.tipo == "redacao"
