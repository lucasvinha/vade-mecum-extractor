# ADR-002 — Parser genérico, com particularidades em perfis por norma

**Status:** aceito em 2026-10-26 (era a decisão D2 do PRD)

## Problema

O primeiro alvo é o Código Penal, mas o edital cobre outras normas com convenções diferentes: a
NSCGJ usa "Alterado"/"Acrescentado" em vez de "Redação dada"/"Incluído", a lei estadual usa
`Artigo 1°` em vez de `Art. 1º`, e o PDF montado é um recorte com lacunas de numeração. Um parser
escrito para o CP quebraria a cada norma nova.

## Opções discutidas

| Opção | A favor | Contra |
|---|---|---|
| Um parser por norma | Cada um simples no começo | Duplicação; correção num não chega aos outros |
| Parser único com `if norma == ...` | Um só lugar | A lógica de cada norma se espalha pelo parser |
| Parser único + perfil de configuração por norma | Norma nova é um `.toml`; o parser só conhece conceitos | O perfil precisa expor tudo o que varia |

## Decisão

O parser é **genérico**, sem lógica fixa do Código Penal. Particularidades de cada norma ficam em
**perfis de configuração**.

Um perfil `padrao` cobre os casos comuns e os específicos sobrescrevem só as diferenças. O que um
perfil pode configurar está em [negocio/pipeline-e-perfis.md](../negocio/pipeline-e-perfis.md).

## Consequências

- Proibido `if norma == ...` no parser; fase que precisaria disso volta para a spec.
- Norma nova entra por perfil `.toml` em `src/vademecum/perfis/`.
- O contrato `LinhaFonte` isola o parser da fonte (HTML ou PDF).

## Histórico
