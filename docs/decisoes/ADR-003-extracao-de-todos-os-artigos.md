# ADR-003 — A extração traz todos os artigos da norma

**Status:** aceito em 2026-10-26 (era a decisão D3 do PRD)

## Problema

O edital pede só parte de cada norma (por exemplo, arts. 121–130 do CP). A extração poderia já
filtrar esses artigos, ou gerar a norma inteira e deixar o filtro para outro passo.

## Opções discutidas

| Opção | A favor | Contra |
|---|---|---|
| Extrair só os artigos pedidos | Saída menor | Mudou o recorte, relê a fonte; a validação de numeração não roda sobre a norma inteira |
| Extrair tudo e recortar depois | Base reaproveitável para qualquer recorte; validação completa (A1) | Base maior |

## Decisão

A extração da fonte bruta traz **todos** os artigos da norma.

O recorte é um comando à parte (`recortar`), que filtra a base pronta sem reler a fonte (RF18).

## Consequências

- A base do CP vai do art. 1 ao 361, e a ausência de lacuna vira critério de aceite (A1).
- Mudar o recorte não exige extrair de novo.
- Quando a fonte já é um recorte (PDF montado), a base traz o que a fonte tem, e a validação de
  lacunas é desligada pelo perfil.

## Histórico

- 2026-10-31: reafirmado. Em 2026-10-30 o operador cogitou deixar o filtro para o Claude; decidiu
  que o Python recorta e o Claude recebe só o recorte.
