"""Compara pares de bases antes/depois para o roteiro de regressão (docs/processo/REGRESSAO.md).

Uso: `python scripts/comparar_bases.py <pasta antes> <pasta depois>`. Cada pasta tem
`<cenario>.json` e `<cenario>.relatorio.json`, gerados pelo `extrair`.
Ignora só o que varia por natureza (`capturado_em`); o resto da saída é determinístico (RNF03).
O resumo separa o nó que saiu da árvore e entrou no relatório como `descarte` (efeito do filtro de
vigência) do nó que sumiu ou mudou sem rastro, que é o que pede atenção.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_IGNORAR = {"capturado_em"}


def _limpar(valor):
    if isinstance(valor, dict):
        return {k: _limpar(v) for k, v in valor.items() if k not in _IGNORAR}
    if isinstance(valor, list):
        return [_limpar(v) for v in valor]
    return valor


def _ler(caminho: Path):
    return _limpar(json.loads(caminho.read_text(encoding="utf-8")))


def _nos(artigos) -> dict[str, str]:
    """id → nó sem os filhos, serializado; a mudança de um filho conta só no filho."""
    saida: dict[str, str] = {}
    pilha = list(artigos)
    while pilha:
        no = pilha.pop()
        pilha.extend(no.get("filhos", []))
        proprio = {k: v for k, v in no.items() if k != "filhos"}
        saida[no["id"]] = json.dumps(proprio, ensure_ascii=False, sort_keys=True)
    return saida


def _chave(entrada: dict) -> str:
    return f"{entrada.get('tipo')}/{entrada.get('motivo', '-')}"


def comparar(antes_dir: Path, depois_dir: Path, cenario: str) -> list[str]:
    linhas = [f"## {cenario}"]
    base_a, base_d = _ler(antes_dir / f"{cenario}.json"), _ler(depois_dir / f"{cenario}.json")
    rel_a = _ler(antes_dir / f"{cenario}.relatorio.json")
    rel_d = _ler(depois_dir / f"{cenario}.relatorio.json")

    for chave in sorted(set(base_a) | set(base_d)):
        if chave != "artigos" and base_a.get(chave) != base_d.get(chave):
            linhas.append(f"- base.{chave} mudou: {base_a.get(chave)!r} → {base_d.get(chave)!r}")

    nos_a, nos_d = _nos(base_a.get("artigos", [])), _nos(base_d.get("artigos", []))
    descartados = {e.get("id") for e in rel_d.get("entradas", []) if e.get("tipo") == "descarte"}
    sairam = sorted(set(nos_a) - set(nos_d))
    # um nó sai com o ancestral descartado: `art121.p2.i6` cobre `art121.p2.i6.a`
    sem_rastro = [
        i for i in sairam if not any(i == d or i.startswith(f"{d}.") for d in descartados if d)
    ]
    entraram = sorted(set(nos_d) - set(nos_a))
    mudaram = sorted(i for i in set(nos_a) & set(nos_d) if nos_a[i] != nos_d[i])
    linhas.append(
        f"- nós: antes {len(nos_a)} · depois {len(nos_d)} · saíram {len(sairam)} "
        f"({len(sairam) - len(sem_rastro)} com descarte no relatório) · entraram {len(entraram)} "
        f"· mudaram {len(mudaram)}"
    )
    for titulo, ids in (("saíram sem descarte", sem_rastro), ("entraram", entraram)):
        if ids:
            linhas.append(f"- {titulo}: {', '.join(ids[:20])}{' …' if len(ids) > 20 else ''}")
    for i in mudaram[:10]:
        linhas.append(f"- mudou {i}:\n  antes  {nos_a[i]}\n  depois {nos_d[i]}")

    cont_a = Counter(_chave(e) for e in rel_a.get("entradas", []))
    cont_d = Counter(_chave(e) for e in rel_d.get("entradas", []))
    for chave in sorted(set(cont_a) | set(cont_d)):
        if cont_a[chave] != cont_d[chave]:
            linhas.append(f"- relatório {chave}: {cont_a[chave]} → {cont_d[chave]}")
    avisos_novos = sorted(
        {e["texto"] for e in rel_d.get("entradas", []) if e.get("tipo") == "aviso"}
        - {e["texto"] for e in rel_a.get("entradas", []) if e.get("tipo") == "aviso"}
    )
    for texto in avisos_novos:
        linhas.append(f"- aviso novo: {texto}")
    textos_d = {e.get("texto") for e in rel_d.get("entradas", [])}
    perdidos = [e for e in rel_a.get("entradas", []) if e.get("texto") not in textos_d]
    if perdidos:
        linhas.append(f"- entradas do relatório antes sem texto igual depois: {len(perdidos)}")
        linhas.extend(
            f"  - {_chave(e)} {e.get('origem')}: {e.get('texto')!r}" for e in perdidos[:10]
        )
    return linhas


def main(argv: list[str]) -> int:
    antes_dir, depois_dir = Path(argv[0]), Path(argv[1])
    cenarios = sorted(
        p.name.removesuffix(".json")
        for p in depois_dir.glob("*.json")
        if not p.name.endswith(".relatorio.json")
    )
    for cenario in cenarios:
        if not (antes_dir / f"{cenario}.json").exists():
            print(f"## {cenario}\n- sem par em {antes_dir}\n")
            continue
        print("\n".join(comparar(antes_dir, depois_dir, cenario)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
