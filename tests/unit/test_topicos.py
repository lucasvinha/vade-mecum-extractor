"""Esquema `topicos-oj/2` de `claude/topicos-oj2026.json` (ver ADR-005 e negocio/recorte-e-cli)."""

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TOPICOS = json.loads((RAIZ / "claude" / "topicos-oj2026.json").read_text(encoding="utf-8"))
GRUPOS_DE_LEI = [
    (materia["id"], grupo)
    for materia in TOPICOS["materias"]
    if materia["tipo"] == "lei"
    for grupo in materia["grupos"]
]
_ID_DE_NORMA = re.compile(r"[a-z][a-z0-9_]*")


def test_adr005_esquema_e_topicos_oj_2():
    assert TOPICOS["schema"] == "topicos-oj/2"


def test_adr005_todo_grupo_de_materia_lei_tem_norma():
    sem_norma = [
        (materia, grupo["titulo"]) for materia, grupo in GRUPOS_DE_LEI if "norma" not in grupo
    ]
    assert sem_norma == []


def test_adr005_norma_e_id_de_perfil_ou_null_sem_artigos():
    # `null` só em grupo que não é lei: nenhum item dele tem `arts` (o grupo "Atualidades").
    for materia, grupo in GRUPOS_DE_LEI:
        norma = grupo["norma"]
        if norma is None:
            assert all("arts" not in item for item in grupo["itens"]), (materia, grupo["titulo"])
        else:
            assert _ID_DE_NORMA.fullmatch(norma), (materia, norma)


def test_adr005_normas_dos_grupos():
    normas = {grupo["norma"] for _, grupo in GRUPOS_DE_LEI} - {None}
    assert normas == {
        "cc", "cf", "cp", "cpc", "cpp", "lei13146", "lei6830", "lei8429", "lei9099", "lindb",
        "nscgj", "lei_sp10261", "lei_sp11608", "res_cnj354",
    }  # fmt: skip
