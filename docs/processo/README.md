# Processo — como uma mudança acontece

Os roteiros desta pasta servem a qualquer modelo (Claude, Copilot, Gemini) e a quem trabalha
sem IA. No Claude Code, cada um tem um comando em `.claude/commands/` que só manda ler o
roteiro. Os valores do projeto (portões, contrato, o que é proibido) vêm de
[docs/README.md § Parâmetros do processo](../README.md#parâmetros-do-processo).

## Qual caminho

| Mudança | Caminho |
|---|---|
| Correção de uma linha, texto, renomeação local | Commit direto, seguindo o [PADRAO_OURO](../PADRAO_OURO.md) e os portões |
| Vale mais de um commit, mexe em contrato, na subida ou em código usado por vários | [SPEC](SPEC.md) → [FASE](FASE.md), uma fase por vez |
| Antes de abrir o PR | [REVISAO](REVISAO.md) |
| Mudou comportamento observável | [REGRESSAO](REGRESSAO.md) |
| Módulo herdado, antes de refatorá-lo, ou quando a revisão pede | [AUDITORIA](AUDITORIA.md) → item em PENDENCIAS → commit direto ou SPEC |
| Defeito: teste vermelho fora de fase, traceback, log, achado `bug` da revisão ou da auditoria, regressão achada | Depuração (no Claude Code, a skill `depuracao-sistematica`): causa raiz antes da correção, depois commit direto ou SPEC |

## O ciclo

```
/auditoria → lê um módulo inteiro contra o PADRAO_OURO; relatório gitignored e item proposto
/spec  → entrevista e escreve specs/<slug>.md, fatiada em fases (não implementa)
/fase  → implementa UMA fase, roda os portões, sugere o commit e para
         (o operador revisa e commita; /fase de novo até a última, que fecha os docs e apaga a spec)
/revisao   → conformidade com o PADRAO_OURO, linhas sem teste + bugs; relatório gitignored
/regressao → comportamento antes/depois; relatório gitignored
```

**Uma sessão por etapa.** Rode cada comando numa conversa nova (`/clear` antes). O que passa
de uma etapa para a outra é arquivo (a spec, o relatório), não contexto. Isso economiza tokens
e evita que o modelo carregue suposições de uma etapa para a outra. Também torna cada etapa
praticável por uma pessoa sozinha.

Regressão grande é fatiada como uma spec: um bloco por sessão, com relatório entre eles.

[specs/](specs/) vazio significa que não há mudança em curso com mais de um commit pela frente.
