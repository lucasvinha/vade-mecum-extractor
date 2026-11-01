import json

import pytest

from vademecum.cli import main


def _extrair(fonte, saida, *extra):
    return main(["extrair", "--fonte", str(fonte), "--perfil", "cp", "--saida", str(saida), *extra])


def test_rf17_extrair_grava_base_e_relatorio_lado_a_lado(fixtures_dir, tmp_path):
    saida = tmp_path / "cp" / "base.json"
    assert _extrair(fixtures_dir / "html" / "cp_enxertos.mht", saida) == 0
    base = json.loads(saida.read_text(encoding="utf-8"))
    relatorio = json.loads((tmp_path / "cp" / "base.relatorio.json").read_text(encoding="utf-8"))
    assert base["schema_version"] == "1.0"
    assert (base["norma"]["id"], base["norma"]["perfil"], base["norma"]["tipo_fonte"]) == (
        "cp",
        "cp",
        "html",
    )
    assert base["norma"]["fonte"].endswith("del2848compilado.htm")
    assert [a["id"] for a in base["artigos"]][:4] == ["art78", "art121", "art121-A", "art121-B"]
    # RF19: a `origem` fica no relatório, nunca na base.
    assert '"origem"' not in saida.read_text(encoding="utf-8")
    assert all("origem" in entrada for entrada in relatorio["entradas"])


def test_rnf03_duas_execucoes_byte_a_byte_iguais(fixtures_dir, tmp_path):
    fonte = fixtures_dir / "html" / "cp_enxertos.mht"
    for pasta in ("a", "b"):
        assert _extrair(fonte, tmp_path / pasta / "base.json") == 0
    for nome in ("base.json", "base.relatorio.json"):
        primeiro = (tmp_path / "a" / nome).read_bytes()
        assert primeiro == (tmp_path / "b" / nome).read_bytes()
        assert primeiro.endswith(b"}\n") and b"\r\n" not in primeiro


def test_rf06_arquivo_inexistente_sai_com_2(tmp_path, capsys):
    assert _extrair(tmp_path / "nao_existe.htm", tmp_path / "base.json") == 2
    assert "arquivo não encontrado" in capsys.readouterr().err
    assert not (tmp_path / "base.json").exists()


def test_rf06_perfil_inexistente_sai_com_2(fixtures_dir, tmp_path, capsys):
    fonte = fixtures_dir / "html" / "cp_art78.htm"
    codigo = main(["extrair", "--fonte", str(fonte), "--perfil", "xx", "--saida", str(tmp_path)])
    assert codigo == 2
    assert "perfil inexistente" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("fonte", "extra", "mensagem"),
    [
        ("https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm", (), "URL"),
        ("LEI_SECA_OJ26.pdf", (), "PDF"),
        ("cp.htm", ("--perfil-auto",), "--perfil-auto"),
    ],
)
def test_entrada_ainda_nao_suportada_sai_com_2(tmp_path, capsys, fonte, extra, mensagem):
    argv = ["extrair", "--fonte", fonte, "--saida", str(tmp_path / "base.json"), *extra]
    assert main(argv) == 2
    assert mensagem in capsys.readouterr().err


def test_saida_dir_ainda_nao_suportada_sai_com_2(tmp_path, capsys):
    assert main(["extrair", "--fonte", "x.pdf", "--saida-dir", str(tmp_path)]) == 2
    assert "--saida-dir" in capsys.readouterr().err


def test_h17_titulo_ausente_sai_vazio_com_aviso(fixtures_dir, tmp_path):
    # `cp_enxertos.mht` é um enxerto sem o cabeçalho do Planalto.
    saida = tmp_path / "base.json"
    assert _extrair(fixtures_dir / "html" / "cp_enxertos.mht", saida) == 0
    base = json.loads(saida.read_text(encoding="utf-8"))
    relatorio = json.loads((tmp_path / "base.relatorio.json").read_text(encoding="utf-8"))
    assert base["norma"]["titulo"] == ""
    assert relatorio["entradas"][0]["tipo"] == "aviso"
    assert relatorio["entradas"][0]["texto"] == "título da norma não encontrado no cabeçalho (H17)"
