import tomllib
from importlib.resources import files

import pytest

import vademecum
from vademecum.cli import main


def test_versao_exposta():
    assert vademecum.SCHEMA_VERSION == "1.0"


def test_perfil_padrao_e_toml_valido():
    perfil = tomllib.loads(files("vademecum.perfis").joinpath("padrao.toml").read_text("utf-8"))
    assert perfil["id"] == "padrao"


def test_cli_exige_subcomando():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2
