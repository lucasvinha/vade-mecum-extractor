from pathlib import Path

import pytest

from vademecum.modelo import (
    Base,
    EntradaRelatorio,
    ErroFonte,
    Metadados,
    No,
    Norma,
    Relatorio,
    chave_de_texto,
    de_json,
    id_artigo,
    relatorio_de_json,
)
from vademecum.recorte import Item, interpretar, recortar

SNAPSHOTS = Path(__file__).resolve().parents[1] / "fixtures" / "snapshots"


def _faixas(expressao):
    return [(item.inicio, item.fim) for item in interpretar(expressao)]


@pytest.mark.parametrize(
    "expressao",
    [
        # `arts` de claude/topicos-oj2026.json.
        "1º a 12",
        "8º; 9º; 18; 19",
        "1.169 a 1.173",
        "396; 396-A",
        "792; 798; 798-A",
        "1.431; 1.432; 1.442; 1.444 a 1.447; 1.451; 1.461; 1.467 a 1.472",
        # MD do conteúdo programático do edital.
        "1º–4º",
        "12; 13",
        "994–1.091; 1.091-A",
        "439; 440; 440-A",
        "196, inciso XX",
        "282, § 1º",
        # Exemplo de negocio/recorte-e-cli.
        "1-12; 100-120; 121; 129; 150; 154; 293-305; 307; 308; 311-A; 312-317",
    ],
)
def test_rf18_linhas_reais_do_edital_sao_aceitas(expressao):
    assert interpretar(expressao)


def test_separador_de_item_ponto_e_virgula_ou_virgula():
    assert _faixas("8º; 9º") == _faixas("8º, 9º") == [((8, ()), (8, ())), ((9, ()), (9, ()))]


@pytest.mark.parametrize("expressao", ["1º a 12", "1º–12", "1º-12", "1 - 12"])
def test_faixa_com_hifen_travessao_ou_a(expressao):
    assert _faixas(expressao) == [((1, ()), (12, ()))]


@pytest.mark.parametrize(
    ("expressao", "faixa"),
    [
        ("1º–4º", ((1, ()), (4, ()))),  # H11: ordinal nas duas pontas
        ("1.169 a 1.173", ((1169, ()), (1173, ()))),  # P13: milhar nas duas pontas
        ("994–1.091", ((994, ()), (1091, ()))),
    ],
)
def test_h11_p13_ordinal_e_milhar_opcionais_nas_pontas(expressao, faixa):
    assert _faixas(expressao) == [faixa]


@pytest.mark.parametrize(
    ("expressao", "faixa"),
    [
        ("359-M-A", ((359, ("M", "A")), (359, ("M", "A")))),  # H12: letra depois de `-` é sufixo
        ("121-A–130", ((121, ("A",)), (130, ()))),
        ("994-1.091", ((994, ()), (1091, ()))),  # dígito depois de `-` fecha a faixa
    ],
)
def test_h12_hifen_com_letra_e_sufixo_e_com_digito_e_faixa(expressao, faixa):
    assert _faixas(expressao) == [faixa]


def test_p1_avulso_e_so_o_artigo_citado():
    [item] = interpretar("121")
    assert item == Item(texto="121", inicio=(121, ()), fim=(121, ()))


def test_adr004_faixa_guarda_as_chaves_das_pontas():
    [item] = interpretar(" 121-130 ")
    assert item == Item(texto="121-130", inicio=(121, ()), fim=(130, ()))


@pytest.mark.parametrize(
    ("expressao", "qualificadores"),
    [
        ("196, inciso XX", ("inciso XX",)),
        ("282, § 1º", ("§ 1º",)),
        ("196, incisos XX; XXI", ("incisos XX", "XXI")),
    ],
)
def test_p2_qualificador_fica_preso_ao_item_anterior(expressao, qualificadores):
    [item] = interpretar(expressao)
    assert item.qualificadores == qualificadores
    assert item.inicio == item.fim


def test_p2_qualificador_nao_passa_para_o_item_seguinte():
    itens = interpretar("196, inciso XX; 197")
    assert [item.qualificadores for item in itens] == [("inciso XX",), ()]


def test_itens_saem_na_ordem_escrita():
    assert [item.texto for item in interpretar("120-125; 121")] == ["120-125", "121"]


@pytest.mark.parametrize(
    ("expressao", "mensagem"),
    [
        ("inciso XX", "qualificador sem artigo antes.*'inciso XX'"),
        ("abc", "qualificador sem artigo antes.*'abc'"),  # não começa com dígito
        ("121-", "ilegível.*'121-'"),
        ("121-a", "ilegível.*'121-a'"),
        ("1-2-3", "ilegível.*'1-2-3'"),
        ("121; 12x", "ilegível.*'12x'"),
        ("130-121", "faixa invertida.*'130-121'"),
        ("121-A–121", "faixa invertida.*'121-A–121'"),
        ("", "item vazio"),
        ("121;; 122", "item vazio"),
    ],
)
def test_expressao_invalida_levanta_erro_fonte_com_o_item(expressao, mensagem):
    with pytest.raises(ErroFonte, match=mensagem):
        interpretar(expressao)


def _artigo(rotulo):
    numero, sufixo = chave_de_texto(rotulo)
    return No(
        id=id_artigo(numero, sufixo),
        tipo="artigo",
        texto=f"texto do art. {rotulo}",
        origem="",
        rotulo=f"Art. {rotulo}",
        numero=numero,
        sufixo=sufixo,
    )


def _base(*rotulos):
    norma = Norma("cp", "Código Penal", None, "html", "cp.htm", "2026-10-26T02:03:12Z", "0", "cp")
    return Base(norma=norma, metadados=Metadados(), artigos=tuple(map(_artigo, rotulos)))


def _recortar(base, expressao, descartes=()):
    relatorio = Relatorio()
    recorte = recortar(base, interpretar(expressao), descartes, relatorio)
    return [artigo.rotulo.removeprefix("Art. ") for artigo in recorte.artigos], relatorio.entradas


def _descarte(id_, origem="html:p#9"):
    return EntradaRelatorio(
        tipo="descarte", origem=origem, texto=f"{id_} (Revogado)", id=id_, motivo="revogado"
    )


def test_p1_avulso_nao_traz_o_artigo_com_letra():
    artigos, entradas = _recortar(_base("120", "121", "121-A", "122"), "121")
    assert (artigos, entradas) == (["121"], ())


def test_p1_artigo_com_letra_entra_se_citado():
    artigos, _ = _recortar(_base("311", "311-A", "312"), "311-A")
    assert artigos == ["311-A"]


def test_rf18_saida_na_ordem_da_base_e_cada_artigo_uma_vez():
    base = _base("120", "121", "122", "123", "124", "125", "126")
    artigos, entradas = _recortar(base, "125; 120-125; 121")
    assert (artigos, entradas) == (["120", "121", "122", "123", "124", "125"], ())


def test_rf18_recorte_mantem_norma_e_metadados_da_base():
    base = _base("1", "2")
    recorte = recortar(base, interpretar("2"), (), Relatorio())
    assert (recorte.norma, recorte.metadados, recorte.recorte) == (base.norma, base.metadados, None)


@pytest.mark.parametrize("expressao", ["999", "200-210"])
def test_item_que_nao_alcanca_artigo_gera_aviso(expressao):
    artigos, [aviso] = _recortar(_base("121", "122"), f"121; {expressao}")
    assert artigos == ["121"]
    assert (aviso.tipo, aviso.origem) == ("aviso", expressao)
    assert expressao in aviso.texto


def test_p2_qualificador_gera_aviso_e_o_artigo_entra_inteiro():
    artigos, [aviso] = _recortar(_base("195", "196", "197"), "196, inciso XX")
    assert artigos == ["196"]
    assert (aviso.tipo, aviso.origem) == ("aviso", "196")
    assert "P2" in aviso.texto and "inciso XX" in aviso.texto


def test_p4_descarte_do_artigo_recortado_e_copiado_sem_mudanca():
    descartes = (
        EntradaRelatorio(tipo="aviso", origem="html:p#1", texto="outro aviso"),
        _descarte("art121.p2-A"),
        _descarte("art122.p1"),
    )
    _, entradas = _recortar(_base("121", "122"), "121", descartes)
    assert entradas == (descartes[1],)


def test_p4_item_so_nos_descartes_entra_sem_aviso():
    # CP: o art. 189 está revogado; o descarte dele já diz isso à Etapa 2.
    descartes = (_descarte("art188"), _descarte("art189"), _descarte("art190"))
    artigos, entradas = _recortar(_base("186", "200"), "189", descartes)
    assert (artigos, entradas) == ([], (descartes[1],))


def test_p4_descarte_sem_id_nao_e_ligado_a_artigo():
    sem_id = EntradaRelatorio(tipo="descarte", origem="html:p#3", texto="Art. 121", motivo="vazio")
    _, entradas = _recortar(_base("121"), "121", (sem_id,))
    assert entradas == ()


def test_rf18_recorte_dos_enxertos_do_cp():
    base = de_json((SNAPSHOTS / "cp_enxertos.json").read_text(encoding="utf-8"))
    relatorio_base = relatorio_de_json(
        (SNAPSHOTS / "cp_enxertos.relatorio.json").read_text(encoding="utf-8")
    )
    relatorio = Relatorio()
    recorte = recortar(base, interpretar("121; 187-189"), relatorio_base.entradas, relatorio)
    assert [artigo.id for artigo in recorte.artigos] == ["art121"]
    ids = [entrada.id for entrada in relatorio.entradas]
    assert ids == ["art121.p2.i6", "art121.p2-A", "art121.p7", "art187", "art188", "art189"]
