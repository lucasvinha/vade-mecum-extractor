"""Interface de linha de comando (ver docs/negocio/recorte-e-cli.md).

Os subcomandos já têm a assinatura definitiva; o que ainda falta de cada um está
na fila de docs/PENDENCIAS.md. Com `fontes/*`, é o único módulo que faz I/O.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from vademecum import __version__
from vademecum.conferencia import conferir
from vademecum.curadoria import validar_curadoria
from vademecum.fontes.html import ler_html
from vademecum.modelo import (
    Base,
    EntradaRelatorio,
    ErroFonte,
    Norma,
    Recorte,
    Relatorio,
    de_json,
    para_json,
    relatorio_de_json,
)
from vademecum.normalizador import normalizar
from vademecum.parser import analisar
from vademecum.perfil import carregar_perfil
from vademecum.recorte import expressao_dos_topicos, interpretar, recortar
from vademecum.render import renderizar
from vademecum.validador import validar
from vademecum.vigencia import filtrar_vigentes

_URL = re.compile(r"^https?://", re.IGNORECASE)
_SUFIXO_RELATORIO = ".relatorio.json"  # `base.json` → `base.relatorio.json`
_SEM_TITULO = "título da norma não encontrado no cabeçalho (H17)"


def _parser() -> argparse.ArgumentParser:
    raiz = argparse.ArgumentParser(prog="vademecum", description=__doc__)
    raiz.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = raiz.add_subparsers(dest="comando", required=True)

    extrair = sub.add_parser("extrair", help="lê a fonte bruta e gera a base completa")
    extrair.add_argument("--fonte", required=True, help="URL, .htm/.html, .mht/.mhtml ou .pdf")
    perfil = extrair.add_mutually_exclusive_group()
    perfil.add_argument("--perfil", default="padrao", help="perfil da norma (padrão: padrao)")
    perfil.add_argument(
        "--perfil-auto", action="store_true", help="PDF multi-norma: perfil por título"
    )
    saida = extrair.add_mutually_exclusive_group(required=True)
    saida.add_argument("--saida", type=Path, help="caminho do JSON da base")
    saida.add_argument("--saida-dir", type=Path, help="diretório com um JSON por norma")

    recortar = sub.add_parser("recortar", help="filtra uma base existente")
    recortar.add_argument("--base", required=True, type=Path)
    selecao = recortar.add_mutually_exclusive_group(required=True)
    selecao.add_argument("--artigos", help='ex.: "1-12; 121; 311-A"')
    selecao.add_argument("--topicos", type=Path, help="JSON dos tópicos do edital (topicos-oj/2)")
    recortar.add_argument("--materia", help="id da matéria nos tópicos; exige --topicos")
    recortar.add_argument("--saida", required=True, type=Path)

    conferir = sub.add_parser("conferir", help="confere o texto legal do HTML contra os recortes")
    conferir.add_argument(
        "--recorte", required=True, type=Path, action="append", help="repetível: um por norma"
    )
    conferir.add_argument("--html", required=True, type=Path)

    renderizar = sub.add_parser("renderizar", help="gera o HTML do vade mecum dos recortes")
    renderizar.add_argument("--topicos", required=True, type=Path, help="JSON dos tópicos")
    renderizar.add_argument("--materia", required=True, help="id da matéria nos tópicos")
    renderizar.add_argument(
        "--recorte", required=True, type=Path, action="append", help="repetível: um por norma"
    )
    renderizar.add_argument("--curadoria", type=Path, help="JSON da curadoria (curadoria-vm/1)")
    renderizar.add_argument("--saida", required=True, type=Path, help="caminho do HTML")

    return raiz


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.comando == "extrair":
            _extrair(args)
        elif args.comando == "recortar":
            _recortar(args)
        elif args.comando == "conferir":
            return _conferir(args)
        else:
            return _renderizar(args)
    except ErroFonte as erro:  # erro de entrada: mensagem para o usuário, código 2 (RF06)
        print(f"erro: {erro}", file=sys.stderr)
        return 2
    return 0


def _extrair(args: argparse.Namespace) -> None:
    """Fonte HTML local → base e relatório em JSON, gravados lado a lado (RF17, RNF03)."""
    if args.perfil_auto or args.saida_dir is not None:
        raise ErroFonte("--perfil-auto e --saida-dir são do PDF multi-norma, ainda não suportado")
    if _URL.match(args.fonte):
        raise ErroFonte(f"leitura por URL ainda não suportada: {args.fonte}")
    caminho = Path(args.fonte)
    if caminho.suffix.lower() == ".pdf":
        raise ErroFonte(f"leitura de PDF ainda não suportada: {caminho}")
    perfil = carregar_perfil(args.perfil)
    relatorio = Relatorio()
    lida = ler_html(caminho, relatorio)
    analise = analisar(normalizar(lida.linhas, perfil.prefixos_artigo), perfil, relatorio)
    if analise.titulo is None:
        # `norma.titulo` não é opcional no esquema: sai vazio, e a falta vai ao relatório.
        origem = lida.linhas[0].origem if lida.linhas else ""
        relatorio.registrar(EntradaRelatorio(tipo="aviso", origem=origem, texto=_SEM_TITULO))
    base = Base(
        norma=Norma(
            id=perfil.id,
            titulo=analise.titulo or "",
            ementa=analise.ementa,
            tipo_fonte=lida.tipo_fonte,
            fonte=lida.fonte,
            capturado_em=lida.capturado_em,
            sha256=lida.sha256,
            perfil=args.perfil,
        ),
        metadados=analise.metadados,
        artigos=filtrar_vigentes(analise.artigos, perfil, relatorio),  # ADR-001
    )
    validar(base, perfil, relatorio)  # V1–V6: só avisa, não muda o código de saída
    _gravar(base, relatorio, args.saida)


def _relatorio_de(caminho: Path) -> Path:
    return caminho.with_name(caminho.name.removesuffix(".json") + _SUFIXO_RELATORIO)


def _gravar(base: Base, relatorio: Relatorio, saida: Path) -> None:
    """Base e relatório lado a lado, com quebra de linha LF em qualquer sistema (RNF02, RNF03)."""
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(para_json(base), encoding="utf-8", newline="\n")
    _relatorio_de(saida).write_text(para_json(relatorio), encoding="utf-8", newline="\n")


def _ler(caminho: Path, descricao: str) -> str:
    try:
        return caminho.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ErroFonte(f"{descricao} não encontrado: {caminho}") from None


def _ler_json(caminho: Path, descricao: str, nome: str) -> Any:
    try:
        return json.loads(_ler(caminho, descricao))
    except json.JSONDecodeError as erro:
        raise ErroFonte(f"{nome} com JSON inválido: {caminho} ({erro})") from None


def _expressao(args: argparse.Namespace, norma: str) -> str:
    """A de `--artigos`, ou a da matéria nos tópicos para a norma da base (ADR-005)."""
    if args.topicos is None:
        if args.materia is not None:
            raise ErroFonte("--materia exige --topicos")
        return args.artigos.strip()
    if args.materia is None:
        raise ErroFonte("--topicos exige --materia")
    topicos = _ler_json(args.topicos, "arquivo dos tópicos", "tópicos")
    return expressao_dos_topicos(topicos, args.materia, norma)


def _recortar(args: argparse.Namespace) -> None:
    """Base e relatório gravados → recorte e relatório do recorte, sem reler a fonte (RF18)."""
    caminho: Path = args.base
    base = de_json(_ler(caminho, "arquivo da base"))
    relatorio_base = relatorio_de_json(_ler(_relatorio_de(caminho), "relatório da base"))
    expressao = _expressao(args, base.norma.id)
    relatorio = Relatorio()
    recorte = recortar(base, interpretar(expressao), relatorio_base.entradas, relatorio)
    # Só o nome do arquivo: o recorte não pode depender da pasta de onde se roda (RNF03).
    origem = Recorte(expressao=expressao, origem=caminho.name)
    recorte = dataclasses.replace(recorte, recorte=origem)
    _gravar(recorte, relatorio, args.saida)


def _conferir(args: argparse.Namespace) -> int:
    """Recortes + HTML do vade mecum → uma linha por divergência; 0 sem nenhuma, 1 com (ADR-005)."""
    recortes = [de_json(_ler(caminho, "arquivo do recorte")) for caminho in args.recorte]
    divergencias = conferir(recortes, _ler(args.html, "arquivo HTML"))
    for divergencia in divergencias:
        print(divergencia)
    return 1 if divergencias else 0


def _renderizar(args: argparse.Namespace) -> int:
    """Tópicos, recortes e curadoria → HTML do vade mecum (ADR-006).

    Erro de curadoria sai 1, uma linha por erro, sem gravar o HTML; o aviso de teto vai para o
    stderr e não muda o código de saída.
    """
    topicos = _ler_json(args.topicos, "arquivo dos tópicos", "tópicos")
    recortes = [
        (
            de_json(_ler(caminho, "arquivo do recorte")),
            relatorio_de_json(_ler(_relatorio_de(caminho), "relatório do recorte")),
        )
        for caminho in args.recorte
    ]
    if args.curadoria is not None:
        dados = _ler_json(args.curadoria, "arquivo da curadoria", "curadoria")
        validacao = validar_curadoria(dados, [base for base, _ in recortes])
        for aviso in validacao.avisos:
            print(f"aviso: {aviso}", file=sys.stderr)
        for erro in validacao.erros:
            print(erro)
        if validacao.erros:
            return 1
    html = renderizar(topicos, args.materia, recortes)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(html, encoding="utf-8", newline="\n")  # LF em qualquer sistema (RNF03)
    return 0
