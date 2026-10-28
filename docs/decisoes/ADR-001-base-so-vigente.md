# ADR-001 — A base contém somente texto vigente

**Status:** aceito em 2026-10-26 (era a decisão D1 do PRD)

## Problema

A fonte do Planalto traz, misturados ao texto vigente, dispositivos revogados e vetados
(47 notas "Revogado" e 17 "Vetado" só no Código Penal). O material de estudo da Etapa 2 parte do
texto que vale hoje; carregar o que caiu obrigaria todo consumidor a filtrar de novo. Ao mesmo
tempo, saber que um dispositivo foi revogado ou deslocado é útil como ponto de atenção (o
feminicídio saiu do art. 121, § 2º, VI e virou o art. 121-A).

## Opções discutidas

| Opção | A favor | Contra |
|---|---|---|
| Base só com o vigente; descartes no relatório | Base limpa para a Etapa 2; nada some sem registro (RNF04) | O histórico fica fora da árvore |
| Base com tudo, marcando `revogado: true` | Histórico no mesmo arquivo | Todo consumidor filtra; recorte e validação ficam mais complexos |

## Decisão

A base contém **somente texto vigente**. Dispositivos revogados ou vetados são descartados da
base e listados no relatório de extração.

O relatório guarda os descartes de forma estruturada (JSON), para a Etapa 2 consultar sem que eles
entrem na base.

## Consequências

- A regra de "o que é revogado" precisa ser precisa, para não descartar texto vigente (H15:
  "Revogado o livramento…" é vigente). Ver [negocio/vigencia-e-notas.md](../negocio/vigencia-e-notas.md).
- Rubrica que fica órfã com o descarte sai junto (H16).
- Reconstruir redações anteriores fica fora do escopo.

## Histórico
