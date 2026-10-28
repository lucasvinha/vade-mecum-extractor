# Parsing — regras de negócio

**O que o sistema decide**, não como o código faz isso. A arquitetura está no
[PADRAO_OURO](../PADRAO_OURO.md) e as decisões em [decisoes/](../decisoes/). As âncoras são
nomes de função ou de módulo. Em divergência com o código, **vale o código**.

Como as linhas normalizadas viram a árvore artigo › parágrafo › inciso › alínea. Usado por
`normalizador.py` e `parser.py`. Vizinhos: [fontes.md](fontes.md) (de onde vêm as linhas, H* e
P*), [vigencia-e-notas.md](vigencia-e-notas.md) (notas e descartes) e
[modelo-de-dados.md](modelo-de-dados.md) (o nó resultante).

## §1. Requisitos

- **RF07** — Reconhecer níveis hierárquicos configuráveis, com nome na linha seguinte e nota antes ou depois do nome (H5, H18). Hierarquia ausente não é erro (P8).
- **RF08** — Reconhecer dispositivos: artigo (inclusive sufixos simples e compostos e milhar: H11, H12, P13), `§ n` e `Parágrafo único`, inciso romano, alínea `a)`, item numérico (`1.`, `2.`; reservado para outras normas).
- **RF09** — Reconhecer a linha `Pena –` como nó posicional do dispositivo corrente (H14).
- **RF10** — Reconhecer rubrica (bloco em negrito no HTML; heurística no PDF) e ligá-la ao próximo dispositivo de qualquer nível (H6).
- **RF11** — Juntar continuação de linha ao dispositivo corrente: linha que não abre dispositivo, título, rubrica nem nota é continuação. No PDF, aplicar a regra do hífen (P14).

## §2. Regras de reconhecimento (ponto de partida)

Os regex abaixo são o **ponto de partida** e devem ser cobertos por testes com as linhas reais dos casos de aceite ([PADRAO_OURO](../PADRAO_OURO.md)). São aplicados **depois** da normalização (ordinal → `º`, travessão → `-`). Na tabela, `\|` é só o escape do Markdown: no código, use `|`. Os padrões de artigo e parágrafo já foram testados contra linhas reais das duas fontes (`Art 187.`, `Art. 359-M-A.`, `Artigo 1°`, `Art. 1.091-A`, `§ 2o-A`, `§ 2°`).

| Elemento | Padrão |
|---|---|
| Artigo | `^(Art\.?\|Artigo)\s*(\d{1,3}(?:\.\d{3})*)\s*º?((?:-[A-Z])*)\s*[-.]?\s*(.*)$` |
| Parágrafo | `^§\s*(\d+)\s*º?((?:-[A-Z])*)\s*[-.]?\s*(.*)$` |
| Parágrafo único | `^Parágrafo\s+único\s*[-.:]?\s*(.*)$` (sem diferenciar maiúsculas) |
| Inciso | `^([IVXLCDM]+)\s*-\s*(.*)$` (no PDF, exigir rótulo em negrito para evitar falso positivo) |
| Alínea | `^([a-z])\)\s*(.*)$` |
| Pena | `^Pena\s*-\s*(.*)$` |
| Nível | `^(PARTE\|LIVRO\|TÍTULO\|CAPÍTULO\|Seção\|Subseção)\b\s*([IVXLC\d]*)` (centralizado) |
| Nota | `\((?:Redação dada\|Incluíd[oa]\|Revogad[oa]s?\|Vide\|Vigência\|VETADO\|Alterad[oa]\|Acrescentad[oa]\|NR)[^)]*\)` + `\bVigência\s*$` |

**Regex só muda com teste:** toda alteração de padrão vem com o caso real que a motivou.

## §3. Armadilhas e limites conhecidos

- **Rubrica no PDF** (pendência P5): não há rubricas na amostra atual, mas normas penais em PDF
  terão. Heurística proposta: linha curta, sem pontuação final, imediatamente antes de
  dispositivo. Validar quando houver PDF de norma penal.
- `Pena` não encerra o dispositivo (H14); `Revogado` no início do texto não é revogação (H15).
- `Parágrafo único.` no meio da linha não é quebrado automaticamente: vira aviso (P15).
