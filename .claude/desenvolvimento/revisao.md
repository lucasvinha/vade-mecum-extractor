# Revisão

## Checklist (aplicar a toda mudança antes de commit)

**Qualidade**
- [ ] `ruff check .` e `ruff format --check .` sem erros
- [ ] `pytest` verde; nenhum teste pulado sem motivo declarado

**Requisitos**
- [ ] Cada regra nova cita o ID do PRD (H*, P*, RF*, D*, V*, A*) no teste ou comentário
- [ ] Mudança de regex acompanhada do caso real que a motivou
- [ ] Nenhuma lógica específica de norma fora de `perfis/*.toml` (D2)

**Invariantes**
- [ ] Nenhuma perda silenciosa: texto descartado ou não classificado vai ao relatório com `origem` (RNF04)
- [ ] Saída determinística: chaves ordenadas, sem timestamp em `artigos` (RNF03)
- [ ] I/O com `pathlib` e `encoding="utf-8"` explícito (RNF02)
- [ ] Texto legal preservado literalmente

**Regressão**
- [ ] Snapshot alterado? Justificativa registrada no log abaixo

## Log de revisões

Uma entrada por fase concluída ou por regravação de snapshot.

| Data | Fase | O que mudou | Decisões / desvios do PRD | Snapshot regravado? |
|---|---|---|---|---|
| 2026-10-26 | 0 | Estrutura inicial, tooling, CI, PRD movido para `docs/Prd.md` | Python fixado em 3.12 (PRD dizia ≥3.11); envelope ganhou `metadados` (H17/A14) | — |
