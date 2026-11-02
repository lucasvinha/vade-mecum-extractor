"""Interface de linha de comando (ver docs/negocio/recorte-e-cli.md).

Os subcomandos já têm a assinatura definitiva; o que ainda falta de cada um está
na fila de docs/PENDENCIAS.md. Com `fontes/*`, é o único módulo que faz I/O.
"""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from vademecum import __version__
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
from vademecum.recorte import interpretar, recortar
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
    recortar.add_argument("--artigos", required=True, help='ex.: "1-12; 121; 311-A"')
    recortar.add_argument("--saida", required=True, type=Path)

    return raiz


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.comando == "extrair":
            _extrair(args)
        else:
            _recortar(args)
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


def _recortar(args: argparse.Namespace) -> None:
    """Base e relatório gravados → recorte e relatório do recorte, sem reler a fonte (RF18)."""
    caminho: Path = args.base
    base = de_json(_ler(caminho, "arquivo da base"))
    relatorio_base = relatorio_de_json(_ler(_relatorio_de(caminho), "relatório da base"))
    expressao = args.artigos.strip()
    relatorio = Relatorio()
    recorte = recortar(base, interpretar(expressao), relatorio_base.entradas, relatorio)
    # Só o nome do arquivo: o recorte não pode depender da pasta de onde se roda (RNF03).
    origem = Recorte(expressao=expressao, origem=caminho.name)
    recorte = dataclasses.replace(recorte, recorte=origem)
    _gravar(recorte, relatorio, args.saida)
