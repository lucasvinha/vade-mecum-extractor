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
    # (`Â§ 2Âº`), e o texto parava ali, sem o art. 361. O `<meta charset>` faz o libxml2 trocar
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


def test_extensao_desconhecida_levanta_erro_fonte(tmp_path):
    caminho = tmp_path / "norma.txt"
    caminho.write_bytes(b"Art. 1")
    with pytest.raises(ErroFonte, match="extensão não suportada"):
        ler_html(caminho, Relatorio())
