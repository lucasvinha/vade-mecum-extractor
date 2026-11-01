"""Interface de linha de comando (ver docs/negocio/recorte-e-cli.md).

Os subcomandos já têm a assinatura definitiva; cada um é ligado ao pipeline no
marco que o implementa, na fila de docs/PENDENCIAS.md. Com `fontes/*`, é o único
módulo que faz I/O.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from vademecum import __version__
from vademecum.fontes.html import ler_html
from vademecum.modelo import Base, EntradaRelatorio, ErroFonte, Norma, Relatorio, para_json
from vademecum.normalizador import normalizar
from vademecum.parser import analisar
from vademecum.perfil import carregar_perfil

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
    if args.comando != "extrair":
        raise NotImplementedError(f"subcomando '{args.comando}' ainda não implementado")
    try:
        _extrair(args)
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
        artigos=analise.artigos,
    )
    saida: Path = args.saida
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(para_json(base), encoding="utf-8", newline="\n")
    relatorio_json = saida.with_name(saida.name.removesuffix(".json") + _SUFIXO_RELATORIO)
    relatorio_json.write_text(para_json(relatorio), encoding="utf-8", newline="\n")
