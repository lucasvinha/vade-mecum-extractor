import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from vademecum.fontes.html import ler_html
from vademecum.modelo import ErroFonte, Relatorio


@pytest.fixture
def cp(fixtures_dir: Path):
    return ler_html(fixtures_dir / "html" / "cp_enxertos.mht", Relatorio())


@pytest.fixture
def textos(cp) -> list[str]:
    return [linha.texto for linha in cp.linhas]


def _mht(
    pasta: Path,
    html: bytes,
    *,
    data: bytes | None = b"Mon, 26 Oct 2026 02:03:12 GMT",
    tipo: bytes = b"text/html",
) -> Path:
    """`.mht` sintético, no formato do salvo pelo navegador (casos que a fixture real não tem)."""
    cabecalho_data = b"Date: " + data + b"\r\n" if data else b""
    caminho = pasta / "sintetico.mht"
    caminho.write_bytes(
        b"From: <Saved by Blink>\r\n" + cabecalho_data + b"MIME-Version: 1.0\r\n"
        b'Content-Type: multipart/related; type="text/html"; boundary="----limite"\r\n\r\n'
        b"------limite\r\nContent-Type: "
        + tipo
        + b"\r\nContent-Transfer-Encoding: binary\r\n\r\n"
        + html
        + b"\r\n------limite--\r\n"
    )
    return caminho


def test_captura_vem_do_cabecalho_do_mht(cp):
    assert cp.tipo_fonte == "html"
    assert cp.fonte == "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm"
    assert cp.capturado_em == "2026-10-26T02:03:12Z"
    assert len(cp.sha256) == 64
    assert int(cp.sha256, 16) >= 0


def test_rf04_art121_sai_em_linhas_logicas_na_ordem(textos):
    inicio = textos.index("Art. 121. Matar alguem:")  # texto legal literal: "alguem"
    assert textos[inicio - 1 : inicio + 8] == [
        "Homicídio simples",
        "Art. 121. Matar alguem:",
        "Pena - reclusão, de seis a vinte anos.",
        "Caso de diminuição de pena",
        "§ 1º Se o agente comete o crime impelido por motivo de relevante valor social ou moral, "
        "ou sob o domínio de violenta emoção, logo em seguida a injusta provocação da vítima, o "
        "juiz pode reduzir a pena de um sexto a um terço.",
        "Homicídio qualificado",
        "§ 2° Se o homicídio é cometido:",
        "I - mediante paga ou promessa de recompensa, ou por outro motivo torpe;",
        "II - por motivo futil;",
    ]


def test_rf04_art121_rotulos_na_ordem_do_texto(textos):
    rotulos = ["§ 2o-A ", "§ 2º-B. ", "§ 4o ", "§ 7o ", "Art. 121-A. ", "Art. 121-B. "]
    posicoes = [next(i for i, t in enumerate(textos) if t.startswith(r)) for r in rotulos]
    assert posicoes == sorted(posicoes)


def test_h11_ordinal_em_sup_fica_colado_ao_numero(textos):
    # `§ 4<sup><u>o</u></sup> No` e `§ 2<u><sup>o</sup></u>-A` na fonte.
    assert any(t.startswith("§ 4o No homicídio culposo, a pena é aumentada") for t in textos)
    assert "§ 2o-A (Revogado pela Lei nº 14.994, de 2024)" in textos


def test_h3_quebra_do_codigo_fonte_vira_espaco(textos):
    # `Art\n187.` e `§\n1º Se o agente` na fonte.
    assert "Art 187. (Revogado pela Lei nº 9.279, de 14.5.1996)" in textos
    assert any(t.startswith("§ 1º Se o agente comete o crime") for t in textos)


def test_h4_artigos_do_mesmo_paragrafo_saem_em_linhas_separadas(textos):
    # Um só `<p>` com os arts. 187 a 191, separados por `<br>`.
    assert textos[-9:] == [
        "Violação de privilégio de invenção",
        "Art 187. (Revogado pela Lei nº 9.279, de 14.5.1996)",
        "Falsa atribuição de privilégio",
        "Art 188. (Revogado pela Lei nº 9.279, de 14.5.1996)",
        "Usurpação ou indevida exploração de modelo ou desenho privilegiado",
        "Art. 189. (Revogado pela Lei nº 9.279, de 14.5.1996)",
        "Falsa declaração de depósito em modelo ou desenho",
        "Art. 190. (Revogado pela Lei nº 9.279, de 14.5.1996)",
        "Art. 191. (Revogado pela Lei nº 9.279, de 14.5.1996)",
    ]


def test_origem_numera_as_linhas_logicas_em_sequencia(cp):
    assert [linha.origem for linha in cp.linhas[:3]] == ["html:p#1", "html:p#2", "html:p#3"]
    assert cp.linhas[-1].origem == f"html:p#{len(cp.linhas)}"


def test_head_e_comentario_nao_sao_texto_da_norma(textos):
    assert textos[0].startswith("Art. 78 - Durante o prazo da suspensão")
    assert not any("DEL2848compilado" in t or "Recorte de" in t for t in textos)


def test_h1_meta_charset_nao_corrompe_documento_grande(tmp_path):
    # Caso real: no `.mht` inteiro do CP (769 KB), a leitura virava mojibake no art. 266, § 2º
    # (`Â§ 2Âº`), e o texto parava ali, sem o art. 361. O `<meta charset>` fazia o libxml2 trocar
    # de codificação no meio do texto, e o defeito só aparece a partir de ~540 KB. Por isso o
    # teste é sintético: a fixture real tem 35 KB.
    meta = b'<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">'
    corpo = b"".join(b"<p>Art. %d. Aplica\xe7\xe3o \xa7 %d\xba</p>" % (i, i) for i in range(20000))
    fonte = ler_html(_mht(tmp_path, b"<html><head>" + meta + b"</head><body>" + corpo), Relatorio())
    assert len(fonte.linhas) == 20000
    assert fonte.linhas[-1].texto == "Art. 19999. Aplicação § 19999º"


def test_h1_sem_charset_declarado_le_em_windows_1252(tmp_path):
    fonte = ler_html(_mht(tmp_path, b"<p>Art. 1\xba Teste</p>"), Relatorio())
    assert [linha.texto for linha in fonte.linhas] == ["Art. 1º Teste"]


def test_sem_date_capturado_em_vem_do_mtime(tmp_path):
    caminho = _mht(tmp_path, b"<p>Art. 1</p>", data=None)
    instante = datetime(2026, 10, 30, 12, 0, 5, tzinfo=UTC).timestamp()
    os.utime(caminho, (instante, instante))
    fonte = ler_html(caminho, Relatorio())
    assert fonte.capturado_em == "2026-10-30T12:00:05Z"
    assert fonte.fonte == str(caminho)


def test_rnf04_byte_invalido_levanta_erro_fonte(tmp_path):
    # 0x81 não existe em windows-1252: decodificação estrita, nunca `replace`.
    html = b'<meta http-equiv="Content-Type" content="text/html; charset=windows-1252"><p>\x81</p>'
    with pytest.raises(ErroFonte, match="byte inválido"):
        ler_html(_mht(tmp_path, html), Relatorio())


def test_mht_sem_parte_html_levanta_erro_fonte(tmp_path):
    with pytest.raises(ErroFonte, match="sem parte text/html"):
        ler_html(_mht(tmp_path, b"GIF89a", tipo=b"image/gif"), Relatorio())


def test_arquivo_inexistente_levanta_erro_fonte(tmp_path):
    with pytest.raises(ErroFonte, match="não encontrado"):
        ler_html(tmp_path / "nao_existe.mht", Relatorio())


@pytest.fixture
def cp_htm(fixtures_dir: Path) -> Path:
    return fixtures_dir / "html" / "cp_art78.htm"


def test_htm_le_as_mesmas_linhas_do_mht_no_mesmo_trecho(cp, cp_htm):
    # O art. 78 abre os dois enxertos: as linhas, flags e `origem` têm de coincidir.
    htm = ler_html(cp_htm, Relatorio())
    assert htm.linhas[0].texto.startswith("Art. 78 - Durante o prazo da suspensão")
    assert htm.linhas == cp.linhas[: len(htm.linhas)]
    assert htm.linhas[-1].texto.startswith("c) comparecimento pessoal")


def test_h1_htm_sem_charset_declarado_le_em_windows_1252(cp_htm):
    # O `.htm` como o Planalto serve: nem MIME nem `<meta>` declaram o charset.
    assert b"charset=" not in cp_htm.read_bytes().lower()
    textos = [linha.texto for linha in ler_html(cp_htm, Relatorio()).linhas]
    assert any(t.startswith("§ 2° Se o condenado houver reparado o dano") for t in textos)
    assert any(t.startswith("a) proibição de freqüentar determinados lugares;") for t in textos)


def test_htm_captura_vem_do_arquivo(tmp_path, cp_htm):
    caminho = tmp_path / "norma.HTML"
    caminho.write_bytes(cp_htm.read_bytes())
    instante = datetime(2026, 10, 31, 11, 2, 25, tzinfo=UTC).timestamp()
    os.utime(caminho, (instante, instante))
    fonte = ler_html(caminho, Relatorio())
    assert fonte.tipo_fonte == "html"
    assert fonte.fonte == str(caminho)
    assert fonte.capturado_em == "2026-10-31T11:02:25Z"
    assert fonte.sha256 == hashlib.sha256(cp_htm.read_bytes()).hexdigest()


def _htm(pasta: Path, html: bytes) -> Path:
    caminho = pasta / "trecho.htm"
    caminho.write_bytes(html)
    return caminho


def test_referencia_128_a_159_segue_o_windows_1252_como_no_navegador(tmp_path):
    # Bytes reais do CP, art. 77, I, e da CF: o libxml2 lia `&#150;` como o controle U+0096, e o
    # `.mht` (já resolvido pelo navegador) trazia `–`. Regra do HTML5 para essas referências.
    html = (
        b'<p ALIGN="JUSTIFY"><font face="Arial" size="2">&nbsp;&nbsp;\r\nI &#150; aplicada pena'
        b" privativa de liberdade</font></p>\r\n<p>d&#146;Oeste</p>"
    )
    textos = [linha.texto for linha in ler_html(_htm(tmp_path, html), Relatorio()).linhas]
    assert textos == ["I – aplicada pena privativa de liberdade", "d’Oeste"]


def test_rnf04_fecho_de_html_no_meio_nao_trunca_o_documento(tmp_path):
    # Bytes reais do CC (l10406compilada.htm), logo depois do preâmbulo: o libxml2 descartava
    # tudo depois do `</html>`, e o Código inteiro sumia sem erro.
    html = (
        b"<html><body><p>Fa\xe7o saber que o Congresso Nacional decreta e eu sanciono a seguinte"
        b' Lei:</font></body></html></p>\n<p align="CENTER">\n <font face="Arial" size="2">\n'
        b"  P A R T E\r\n\xa0\xa0 G E R A L</font></p>"
    )
    textos = [linha.texto for linha in ler_html(_htm(tmp_path, html), Relatorio()).linhas]
    assert textos[-1] == "P A R T E G E R A L"


def test_extensao_desconhecida_levanta_erro_fonte(tmp_path):
    caminho = tmp_path / "norma.txt"
    caminho.write_bytes(b"Art. 1")
    with pytest.raises(ErroFonte, match="extensão não suportada"):
        ler_html(caminho, Relatorio())


def _linha(fonte, inicio: str):
    return next(linha for linha in fonte.linhas if linha.texto.startswith(inicio))


def test_h5_titulo_e_nome_do_nivel_saem_centralizados_e_em_negrito(cp):
    # `<p align="CENTER"><strong>…TÍTULO I<br>\nDOS CRIMES CONTRA A PESSOA…</strong></p>`.
    titulos = ["TÍTULO I", "DOS CRIMES CONTRA A PESSOA", "CAPÍTULO I", "DOS CRIMES CONTRA A VIDA"]
    for texto in titulos:
        linha = _linha(cp, texto)
        assert (linha.texto, linha.centralizado, linha.negrito) == (texto, True, True)


def test_h6_rubrica_em_negrito_nao_centralizada(cp):
    rubrica = _linha(cp, "Homicídio simples")
    assert (rubrica.negrito, rubrica.rotulo_negrito, rubrica.centralizado) == (True, False, False)


def test_h6_b_so_com_espaco_nao_marca_a_linha_seguinte(cp):
    # Na fonte: `<b>\n\n</b><p align="left"><b></b><font …>&nbsp;…\nArt. 121. Matar alguem:`.
    artigo = _linha(cp, "Art. 121. Matar alguem:")
    assert (artigo.negrito, artigo.rotulo_negrito, artigo.centralizado) == (False, False, False)


def test_linha_sem_negrito_nem_centro_fica_sem_flag(cp):
    assert not any(linha.negrito or linha.rotulo_negrito for linha in cp.linhas[:5])
    assert not any(linha.centralizado for linha in cp.linhas[:5])


def test_rotulo_em_strong_marca_rotulo_negrito(tmp_path):
    # Bytes reais do CP, art. 9º, parágrafo único: só o rótulo está em `<strong>`.
    html = (
        b'<p ALIGN="JUSTIFY"><font SIZE="2" FACE="Arial"><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        b"&nbsp;&nbsp;\r\nPar\xe1grafo \xfanico</strong> - A homologa\xe7\xe3o depende: <a\r\n"
        b'href="../LEIS/1980-1988/L7209.htm#art9">(Inclu\xeddo pela Lei n\xba 7.209, de 11.7.1984)'
        b"</a></font></p>"
    )
    [linha] = ler_html(_htm(tmp_path, html), Relatorio()).linhas
    assert linha.texto.startswith("Parágrafo único - A homologação depende:")
    assert (linha.negrito, linha.rotulo_negrito) == (False, True)


@pytest.fixture
def cp_negrito(fixtures_dir: Path):
    return ler_html(fixtures_dir / "html" / "cp_negrito.htm", Relatorio())


def test_h6_b_fechado_fora_de_ordem_reabre_no_paragrafo_como_no_navegador(cp_negrito):
    # `<b><i>\r\n\r\n<p ALIGN="JUSTIFY"></i>…Tempo do crime</font></b></p>`: pela regra do HTML5,
    # o `<b>` reabre dentro do `<p>`, e o `.mht` salvo pelo navegador traz a rubrica em negrito.
    # O libxml2 não reabria, e 288 rubricas do `.htm` do CP saíam sem negrito (A14).
    rubrica = _linha(cp_negrito, "Tempo do crime")
    assert (rubrica.texto, rubrica.negrito, rubrica.rotulo_negrito) == (
        "Tempo do crime",
        True,
        False,
    )


def test_h6_font_weight_700_no_style_e_negrito(cp_negrito):
    # Rubrica do art. 311-A: `<span style="color: black; font-weight: 700">Fraudes em certames…`,
    # sem `<b>`; a nota `(Incluído…)` vem fora do `<span>`, sem negrito.
    rubrica = _linha(cp_negrito, "Fraudes em certames de interesse público")
    assert (rubrica.negrito, rubrica.rotulo_negrito) == (False, True)


def test_h6_font_weight_normal_tira_o_negrito_do_b(cp_negrito):
    # Art. 298, parágrafo único: `<b><span style="…font-weight: normal">Parágrafo único.` O
    # navegador mostra o rótulo sem negrito; só o `caput`, num `<span>` sem peso, fica no `<b>`.
    paragrafo = _linha(cp_negrito, "Parágrafo único. Para fins do disposto no caput")
    assert (paragrafo.negrito, paragrafo.rotulo_negrito) == (False, False)


def test_h5_text_align_center_no_style_centraliza(tmp_path):
    # Bytes reais do CP, CAPÍTULO V do Título X: centralizado só pelo `style`, sem `align`.
    html = (
        b'<p class="cabea2" style="text-indent: 0; margin-left: 0cm; text-align:center">\r\n\t\t'
        b'<span style="color: black; font-weight: 700">CAP\xcdTULO V<br>\r\n\t\t</span><a href="'
        b'../_Ato2011-2014/2011/Lei/L12550.htm#art19">(Inclu\xeddo \r\n\t\tpela Lei 12.550. de '
        b'2011)</a></p>\r\n\t\t<p class="texto3" style="text-indent: 1cm">Fraudes</p>'
    )
    linhas = ler_html(_htm(tmp_path, html), Relatorio()).linhas
    assert [(linha.texto, linha.centralizado) for linha in linhas] == [
        ("CAPÍTULO V", True),
        ("(Incluído pela Lei 12.550. de 2011)", True),
        ("Fraudes", False),
    ]
