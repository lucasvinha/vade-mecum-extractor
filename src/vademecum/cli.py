"""Interface de linha de comando (ver docs/negocio/recorte-e-cli.md).

Os subcomandos já têm a assinatura definitiva; cada um é ligado ao pipeline no
marco que o implementa, na fila de docs/PENDENCIAS.md.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from vademecum import __version__


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
    raise NotImplementedError(f"subcomando '{args.comando}' ainda não implementado")
