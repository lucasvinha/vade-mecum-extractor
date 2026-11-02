# Spec — Recorte + `recortar` (M5)

> Decisão que executa: ADR-004, ADR-003 e RF18, P1 e P2 de negocio/recorte-e-cli; confirma o §6
> desse documento (operador, 2026-11-01). Nenhum ADR novo. Item: PENDENCIAS #15 (M5).
> Escrita em 2026-11-01 contra `3d349f1`, branch `m5-recorte`.
> Fechada a última fase, este arquivo é apagado (o git preserva).

## Problema

O `recortar` existe só no argparse: `src/vademecum/cli.py:56-57` levanta `NotImplementedError` para
qualquer subcomando que não seja `extrair`, e não há `recorte.py`. Sem ele, a Etapa 2 recebe a base
inteira do CP (361 artigos), quando o edital cobra 87. Nas cinco normas maiores, são 686 dos 4.540
artigos da numeração-base. A ADR-003 manda o Python recortar e o Claude receber só o recorte.

A expressão chega como o edital escreve. Casos reais, que os testes usam literalmente:

- `claude/topicos-oj2026.json`, campo `arts`: `1º a 12`, `8º; 9º; 18; 19`, `1.169 a 1.173`,
  `396; 396-A`, `792; 798; 798-A`, `1.431; 1.432; 1.442; 1.444 a 1.447; 1.451; 1.461; 1.467 a 1.472`.
- O MD do conteúdo programático (fora do git; o operador colou na entrevista): `1º–4º`, `12; 13`,
  `994–1.091; 1.091-A`, `439; 440; 440-A`, `196, inciso XX`, `282, § 1º`.

Quem lê o MD é o modelo (ou o operador), que chama `recortar --artigos "<expressão>"` uma vez por
norma. A CLI não lê o MD nem o arquivo de tópicos.

## Estado final

- `python -m vademecum recortar --base dados/cp/base.json --artigos "1º a 12; 121; 311-A"
  --saida dados/cp/recorte.json` grava o recorte e `recorte.relatorio.json`, e sai com código 0.
- A13 passa (`tests/aceite/test_a13_recorte_faixa.py`): base sintética com 120, 121, 121-A, 121-B,
  122…130, 130-A e 131; o recorte `121-130` traz 121, 121-A, 121-B e 122…130, sem 130-A.
- `para_json(de_json(t)) == t`, byte a byte, sobre `tests/fixtures/snapshots/cp_enxertos.json`, e o
  mesmo vale para o relatório.
- Todas as linhas reais do Problema são aceitas pelo interpretador da expressão.

## Fora do escopo, de propósito

- **Ler o MD ou o `topicos-oj2026.json` na CLI** (`--topico`): o arquivo de tópicos não diz a
  norma de cada item, e o MD mistura normas sem formato estável. Isso ficaria para outro ADR.
- **Recorte abaixo do artigo** (`196, inciso XX`): o artigo inteiro entra, com `aviso` (P2).
- **Validador no recorte:** V2 acusaria toda lacuna entre as faixas. O recorte não roda `validar`.
- **Recorte de PDF multi-norma** (`--saida-dir`): depende do M8.

## Contrato

- **CLI.** `recortar` passa a funcionar, com as opções que já estão no argparse (`--base`,
  `--artigos`, `--saida`). Grava `<saida>` e `<saida sem .json>.relatorio.json`, o mesmo sufixo do
  `extrair`. Código 0 com ou sem `aviso`; código 2 (`ErroFonte`) para: base inexistente; relatório
  da base inexistente; `schema_version` diferente do atual; item ilegível (`abc`, `121-`); faixa
  invertida (`130-121`). A mensagem cita o item ou o arquivo.
- **Base do recorte.** Mesmo esquema da base, sem campo novo. `norma` e `metadados` vêm copiados da
  base; `recorte` = `{"expressao": <texto recebido, sem espaço nas pontas>, "origem": <nome do
  arquivo da base, sem diretório>}`. Assim, a saída não depende da pasta de onde se roda (RNF03).
- **Relatório do recorte.** Mesmo esquema por tipo do relatório da base. Traz:
  - `aviso` para o item ou a faixa que não alcança artigo nenhum, nem na base nem nos descartes;
  - `aviso` para o qualificador ignorado, com o trecho (P2);
  - os `descarte` da base cujo artigo cai no recorte, copiados sem mudança. O artigo sai do `id`
    (`art121.p2-A` → `art121`). Item que só existe nos descartes (`189` no CP) não gera aviso: o
    descarte já diz à Etapa 2 que ele foi revogado.
- **`modelo.py`.** `de_json(texto) -> Base` e `relatorio_de_json(texto) -> Relatorio`. Os nós
  lidos têm `origem` vazio, porque ela não vai ao JSON (RF19). `schema_version` diferente do atual
  levanta `ErroFonte`.
- **Etapa 2.** Recebe o recorte e o relatório do recorte. O esquema que ela lê não muda.

Regras da expressão, do §2 e §6 de negocio/recorte-e-cli, confirmadas em 2026-11-01:

| Regra | Exemplo |
|---|---|
| Separador de item: `;` ou `,` | `8º; 9º`, `12, 13` |
| Faixa: `-`, `–` ou ` a ` | `1º a 12`, `994–1.091`, `293-305` |
| Ordinal e milhar opcionais, nas duas pontas (`modelo.chave_de_texto`) | `1º–4º`, `1.169 a 1.173` |
| Depois de `-`, letra é sufixo e dígito é fim de faixa | `359-M-A`, `121-A–130`, `994-1.091` |
| Depois de `,` ou `;`, texto que não começa com dígito é qualificador do item anterior: `aviso` com o trecho, o artigo inteiro entra (P2) | `196, inciso XX`, `282, § 1º` |
| Qualificador sem item anterior, item ilegível ou faixa invertida: `ErroFonte` | `inciso XX`, `abc`, `121-`, `130-121` |
| Faixa `a–b`: todo artigo com `chave(a) ≤ chave ≤ chave(b)` (ADR-004) | `121-130` sem 130-A |
| Avulso: só o artigo citado (P1) | `121` sem 121-A |
| Saída na ordem da base, cada artigo uma vez | `120-125; 121` → 120…125 |

## Fases

| # | Fase | Toca | Aceite | Modelo | Feito |
|---|---|---|---|---|---|
| 1 | `de_json` e `relatorio_de_json` | `modelo.py`, `tests/unit/test_modelo.py` | portões verdes; ida e volta byte a byte sobre `cp_enxertos.json` e `cp_enxertos.relatorio.json`; `schema_version` errado → `ErroFonte`; nenhum chamador ainda | Sonnet | |
| 2 | Interpretador da expressão | `recorte.py` (novo), `tests/unit/test_recorte.py` (novo) | portões verdes; todas as linhas reais do Problema aceitas; cada linha da tabela de regras com um teste; erros com o item na mensagem | Opus | |
| 3 | Seleção dos artigos e dos descartes + A13 | `recorte.py`, `tests/unit/test_recorte.py`, `tests/aceite/test_a13_recorte_faixa.py` (novo) | portões verdes; A13 passando; avulso (P1), ordem da base sem repetição, aviso de item ausente, descarte copiado sem aviso | Opus | |
| 4 | Subcomando `recortar` | `cli.py`, `tests/unit/test_cli.py` | portões verdes; recorte e relatório gravados lado a lado; `recorte.origem` sem diretório; código 2 para base ou relatório ausente; `recortar` deixa de levantar `NotImplementedError` | Sonnet | |
| 5 | Fechamento | `negocio/recorte-e-cli.md`, `negocio/modelo-de-dados.md`, `docs/README.md`, `PENDENCIAS.md`, esta spec | `scripts/verificar_docs.py` sai 0; spec apagada | Sonnet | |

Notas por fase:

- **Fase 1.** Reconstrói `No`, `Nota`, `Local`, `Norma`, `Metadados`, `Recorte` e
  `EntradaRelatorio` a partir das chaves de `_CHAVES_POR_TIPO`, `_CHAVES_ENTRADA` e
  `_CHAVES_DESCARTE` (`modelo.py:238-248`); lista do JSON vira tupla. Não muda `para_json`.
- **Fase 2.** Função pura `interpretar(expressao) -> tuple[Item, ...]` (faixa ou avulso, com as
  chaves das pontas e o qualificador, se houver). O número de cada ponta passa por
  `modelo.chave_de_texto` (`modelo.py:23`), sem regex nova para o número. A gramática da tabela de
  regras é regex nova: cada padrão leva o caso real que o motivou, no mesmo commit.
- **Fase 3.** `recortar(base, itens, descartes, relatorio) -> Base`: função pura, sem I/O
  (PADRAO_OURO). Os `aviso` saem com `origem` = o item como foi escrito. A base sintética da A13 é
  montada no teste com `No` de artigo, sem fixture.
- **Fase 4.** O nome do relatório da base vem do mesmo sufixo `_SUFIXO_RELATORIO` usado pelo
  `extrair` (`cli.py`).
- **Fase 5.** No recorte-e-cli: as regras do §6 sobem para o §3, o §4 descreve o relatório do
  recorte, o "(proposta)" sai do título do §4 se o `recortar` já bater, e o §6 é apagado. No
  modelo-de-dados: o relatório do recorte ao lado do envelope. No README técnico: `de_json` na linha
  do `modelo.py` e `recorte.py` com a assinatura real no Mapa do código. Em PENDENCIAS: risca o M5
  com data e sha e aponta o M6 em "Agora".

## Em aberto

- **`faixa_revogada` no relatório do recorte.** Só o PDF da NSCGJ gera esse tipo (A10, M8); o CP
  não tem. Nesta spec, o recorte copia só `descarte`. Quem responde: o operador, na spec do M8.
  Não bloqueia nenhuma fase daqui; o M8 tem de decidir antes de recortar a NSCGJ, senão a faixa
  revogada some do recorte.
