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


def test_aviso_do_validador_nao_muda_o_codigo_de_saida(fixtures_dir, tmp_path):
    # O enxerto começa no art. 78: a V2 acusa as lacunas de 1 a 77, e a extração sai com 0.
    saida = tmp_path / "base.json"
    assert _extrair(fixtures_dir / "html" / "cp_enxertos.mht", saida) == 0
    relatorio = json.loads((tmp_path / "base.relatorio.json").read_text(encoding="utf-8"))
    avisos = [e["texto"] for e in relatorio["entradas"] if e["tipo"] == "aviso"]
    assert "V2: lacuna na numeração-base: art. 1" in avisos


def _recortar(base, artigos, saida):
    return main(["recortar", "--base", str(base), "--artigos", artigos, "--saida", str(saida)])


@pytest.fixture
def base_enxertos(fixtures_dir, tmp_path):
    base = tmp_path / "extracao" / "cp_base.json"
    assert _extrair(fixtures_dir / "html" / "cp_enxertos.mht", base) == 0
    return base


def test_rf18_recortar_grava_recorte_e_relatorio_lado_a_lado(base_enxertos, tmp_path):
    saida = tmp_path / "recorte" / "cp_recorte.json"
    assert _recortar(base_enxertos, " 121-130; 189, inciso I ", saida) == 0
    recorte = json.loads(saida.read_text(encoding="utf-8"))
    relatorio = json.loads(
        (tmp_path / "recorte" / "cp_recorte.relatorio.json").read_text(encoding="utf-8")
    )
    base = json.loads(base_enxertos.read_text(encoding="utf-8"))
    assert [a["id"] for a in recorte["artigos"]] == ["art121", "art121-A", "art121-B"]
    assert (recorte["norma"], recorte["metadados"]) == (base["norma"], base["metadados"])
    # RNF03: a origem é só o nome do arquivo, sem a pasta de onde se rodou.
    assert recorte["recorte"] == {"expressao": "121-130; 189, inciso I", "origem": "cp_base.json"}
    tipos = [(e["tipo"], e.get("id")) for e in relatorio["entradas"]]
    assert ("aviso", None) in tipos and ("descarte", "art189") in tipos
    assert ("descarte", "art187") not in tipos


def test_rnf03_recortar_duas_vezes_byte_a_byte_igual(base_enxertos, tmp_path):
    for pasta in ("a", "b"):
        assert _recortar(base_enxertos, "121; 187-191", tmp_path / pasta / "r.json") == 0
    for nome in ("r.json", "r.relatorio.json"):
        primeiro = (tmp_path / "a" / nome).read_bytes()
        assert primeiro == (tmp_path / "b" / nome).read_bytes()
        assert b"\r\n" not in primeiro


def test_rf06_recortar_base_inexistente_sai_com_2(tmp_path, capsys):
    assert _recortar(tmp_path / "nao_existe.json", "121", tmp_path / "r.json") == 2
    assert "arquivo da base não encontrado" in capsys.readouterr().err
    assert not (tmp_path / "r.json").exists()


def test_rf06_recortar_sem_relatorio_da_base_sai_com_2(base_enxertos, tmp_path, capsys):
    (base_enxertos.parent / "cp_base.relatorio.json").unlink()
    assert _recortar(base_enxertos, "121", tmp_path / "r.json") == 2
    assert "relatório da base não encontrado" in capsys.readouterr().err


def test_rf06_recortar_schema_version_diferente_sai_com_2(base_enxertos, tmp_path, capsys):
    dados = json.loads(base_enxertos.read_text(encoding="utf-8"))
    dados["schema_version"] = "0.9"
    base_enxertos.write_text(json.dumps(dados), encoding="utf-8")
    assert _recortar(base_enxertos, "121", tmp_path / "r.json") == 2
    assert "schema_version" in capsys.readouterr().err


@pytest.mark.parametrize("artigos", ["abc", "121-", "130-121"])
def test_rf06_recortar_expressao_invalida_sai_com_2_citando_o_item(
    base_enxertos, tmp_path, capsys, artigos
):
    assert _recortar(base_enxertos, artigos, tmp_path / "r.json") == 2
    assert repr(artigos) in capsys.readouterr().err
    assert not (tmp_path / "r.json").exists()


def _recortar_topicos(base, topicos, materia, saida):
    argv = ["recortar", "--base", str(base), "--topicos", str(topicos), "--saida", str(saida)]
    return main([*argv, "--materia", materia] if materia else argv)


@pytest.fixture
def topicos(tmp_path):
    caminho = tmp_path / "topicos.json"
    grupos = [
        {"titulo": "CP", "norma": "cp", "itens": [{"id": "a", "arts": "121"}, {"id": "b"}]},
        {"titulo": "CPP", "norma": "cpp", "itens": [{"id": "c", "arts": "24"}]},
        {"titulo": "CP", "norma": "cp", "itens": [{"id": "d", "arts": "187-191"}]},
    ]
    materias = [
        {"id": "penal", "tipo": "lei", "grupos": grupos},
        {"id": "civil", "tipo": "lei", "grupos": [grupos[1]]},
    ]
    caminho.write_text(json.dumps({"schema": "topicos-oj/2", "materias": materias}), "utf-8")
    return caminho


def test_adr005_recortar_pela_materia_dos_topicos(base_enxertos, topicos, tmp_path):
    saida = tmp_path / "r.json"
    assert _recortar_topicos(base_enxertos, topicos, "penal", saida) == 0
    recorte = json.loads(saida.read_text(encoding="utf-8"))
    assert recorte["recorte"] == {"expressao": "121; 187-191", "origem": "cp_base.json"}
    assert [a["id"] for a in recorte["artigos"]] == ["art121"]


@pytest.mark.parametrize(
    ("materia", "mensagem"),
    [
        ("xx", "matéria inexistente nos tópicos: 'xx'"),
        ("civil", "nenhum grupo da matéria 'civil' é da norma 'cp'"),
        (None, "--topicos exige --materia"),
    ],
)
def test_adr005_recortar_topicos_com_erro_sai_com_2(
    base_enxertos, topicos, tmp_path, capsys, materia, mensagem
):
    assert _recortar_topicos(base_enxertos, topicos, materia, tmp_path / "r.json") == 2
    assert mensagem in capsys.readouterr().err
    assert not (tmp_path / "r.json").exists()


def test_adr005_recortar_materia_sem_topicos_sai_com_2(base_enxertos, tmp_path, capsys):
    argv = ["recortar", "--base", str(base_enxertos), "--artigos", "121", "--materia", "penal"]
    assert main([*argv, "--saida", str(tmp_path / "r.json")]) == 2
    assert "--materia exige --topicos" in capsys.readouterr().err


def test_adr005_recortar_artigos_e_topicos_juntos_e_erro_de_uso(base_enxertos, topicos, tmp_path):
    argv = ["recortar", "--base", str(base_enxertos), "--artigos", "121", "--topicos", str(topicos)]
    with pytest.raises(SystemExit) as saida:
        main([*argv, "--materia", "penal", "--saida", str(tmp_path / "r.json")])
    assert saida.value.code == 2


@pytest.fixture
def recorte_121(fixtures_dir, tmp_path):
    base = fixtures_dir / "snapshots" / "cp_enxertos.json"
    saida = tmp_path / "recorte" / "cp.json"
    assert _recortar(base, "121", saida) == 0
    return saida


def _conferir(recorte, html):
    return main(["conferir", "--recorte", str(recorte), "--html", str(html)])


def test_adr005_conferir_html_correto_sai_com_0(fixtures_dir, recorte_121, capsys):
    assert _conferir(recorte_121, fixtures_dir / "vade-mecum" / "cp_art121.html") == 0
    assert capsys.readouterr().out == ""


def test_adr005_conferir_com_divergencia_sai_com_1(fixtures_dir, recorte_121, tmp_path, capsys):
    html = (fixtures_dir / "vade-mecum" / "cp_art121.html").read_text(encoding="utf-8")
    alterado = tmp_path / "alterado.html"
    alterado.write_text(html.replace("Matar <mark>alguem</mark>:", "Matar alguém:"), "utf-8")
    assert _conferir(recorte_121, alterado) == 1
    [linha] = capsys.readouterr().out.splitlines()
    assert linha.startswith("cp:art121: campo texto divergente")


def test_adr005_conferir_arquivo_inexistente_sai_com_2(recorte_121, tmp_path, capsys):
    assert _conferir(recorte_121, tmp_path / "nao_existe.html") == 2
    assert "arquivo HTML não encontrado" in capsys.readouterr().err
