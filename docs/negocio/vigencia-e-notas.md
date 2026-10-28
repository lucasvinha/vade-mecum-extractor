# Vigência e notas — regras de negócio

**O que o sistema decide**, não como o código faz isso. A arquitetura está no
[PADRAO_OURO](../PADRAO_OURO.md) e as decisões em [decisoes/](../decisoes/). As âncoras são
nomes de função ou de módulo. Em divergência com o código, **vale o código**.

Como as notas legislativas entre parênteses são extraídas e classificadas, e como elas decidem o
que sai da base. Usado por `notas.py` e `vigencia.py`. A decisão de manter só o texto vigente é o
[ADR-001](../decisoes/ADR-001-base-so-vigente.md). Vizinhos: [parsing.md](parsing.md) (o regex de
nota) e [modelo-de-dados.md](modelo-de-dados.md) (onde a nota fica no nó).

## §1. Extração de notas

- **RF12** — Extrair notas entre parênteses (e "Vigência" sem parênteses) do texto, guardá-las no nó e deixar o `texto` limpo (H9, H10, P10, P16).

## §2. Classificação

| `tipo` | Gatilhos (perfil padrão + NSCGJ) |
|---|---|
| `redacao` | Redação dada, Alterado, (NR) |
| `inclusao` | Incluído/Incluída, Acrescentado |
| `revogacao` | Revogado/Revogada/Revogados |
| `veto` | VETADO, Vetado |
| `vigencia` | Vigência (com ou sem parênteses) |
| `remissao` | Vide |
| `outra` | qualquer parêntese com "Lei nº"/"Provimento" não classificado (vai para o relatório) |

Campos: `norma` (ex.: "Lei nº 15.134", "Provimento CG Nº 48"), `ano`, `data` (quando o texto trouxer a data completa), `bruto`.

O vocabulário de cada tipo vem do perfil da norma ([pipeline-e-perfis.md](pipeline-e-perfis.md)).

## §3. Vigência (ADR-001)

- **RF14** — Descartar dispositivo cujo conteúdo, sem notas, é vazio, `Revogado(s).` ou `(VETADO)`. Descartar junto a rubrica órfã (H15, H16, P12).
- **RF15** — Revogação em faixa (`Art. X a Art. Y. Revogados.`) não gera artigo; vai para o relatório (P11).
- **RF16** — Todo descarte é registrado no relatório com rótulo, motivo e nota de origem.

A revogação é identificada pela **nota** e pelo conteúdo vazio, nunca pela formatação (H8).

## §4. Armadilhas e limites conhecidos

- **Falso positivo:** `Art. 88 - Revogado o livramento…` é texto vigente (H15, caso A4).
- **Regra temporal do edital** (pendência P3): as notas trazem só o ano da lei alteradora, não a
  data. A base guarda número e ano de cada nota; a conferência de data contra o corte do edital
  não é feita aqui.
- **Informação de deslocamento** (pendência P4): o descarte perde "este inciso foi revogado e
  virou outro artigo"; por isso o relatório guarda os descartes de forma estruturada.
