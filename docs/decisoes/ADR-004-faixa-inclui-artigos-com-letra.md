# ADR-004 — No recorte, a faixa inclui os artigos com letra dentro dela

**Status:** aceito em 2026-10-26 (era a decisão D4 do PRD)

## Problema

O edital indica artigos por faixa (`121-130`, `994-1.091`), e a legislação tem artigos com letra
inseridos depois (121-A, 121-B, 1.091-A). É preciso decidir se a faixa os alcança.

## Opções discutidas

| Opção | A favor | Contra |
|---|---|---|
| Faixa só com números inteiros | Literal | Perde 121-A e 121-B, que estão no meio do conteúdo cobrado |
| Faixa pela chave `(numero, sufixo)`, inclusive letras | Bate com o edital, que cita `1.091-A` à parte da faixa `994–1.091` | 130-A fica de fora de `121-130`, o que pode surpreender |

## Decisão

No recorte, uma **faixa** `a–b` inclui os artigos com letra que estão dentro dela (ex.: `121–130`
inclui 121-A e 121-B).

Entra todo artigo com `chave(a) ≤ chave ≤ chave(b)`. Por isso `121–130` não inclui 130-A, que
vem depois de `130`.

## Consequências

- A ordenação e o recorte dependem da mesma chave; ver
  [negocio/recorte-e-cli.md](../negocio/recorte-e-cli.md).
- Artigo avulso (`121`) não é coberto por esta decisão: inclui só ele (P1, confirmada pelo
  operador), regra em [negocio/recorte-e-cli.md](../negocio/recorte-e-cli.md).
- Caso de aceite: A13.

## Histórico

- 2026-10-30: P1 confirmada; a consequência sobre artigo avulso passa a apontar para a regra.
