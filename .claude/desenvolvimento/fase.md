# Fases de implementação

> Sequência do PRD §14. Marque `[x]` ao concluir; uma fase só fecha com o critério de saída
> atendido e o log preenchido em `revisao.md`.

**Fase atual: 1**

## Fase 0 — Setup do projeto ✅
- [x] `pyproject.toml` (hatchling, ruff, pytest), `.python-version`, `.gitignore`
- [x] Pacote `src/vademecum/` com CLI esqueleto e perfil `padrao.toml`
- [x] `.claude/` (CLAUDE.md, settings, desenvolvimento/), `docs/Prd.md`
- [x] CI (ruff + pytest)

**Saída:** `ruff check . && ruff format --check . && pytest` verdes.

## Fase 1 — Modelo, ordenação e recorte
- [ ] `modelo.py`: dataclasses e serialização determinística (spec §4)
- [ ] `chave_ordenacao()` com sufixo simples e composto (H12, §9.2)
- [ ] `recorte.py`: parser da expressão (§9.1) e semântica de faixa (D4)
- [ ] Testes unitários sem depender de fonte

**Saída:** A13 passando com base sintética; ordem `359-M < 359-M-A < 359-M-B < 359-N` testada.

## Fase 2 — Leitor HTML + normalizador
- [ ] `fontes/html.py`: `.mht` e arquivo local (RF03, RF04; H1–H4)
- [ ] `normalizador.py`: ordinais, travessões (H11, H13)

**Saída:** trecho do art. 121 vira linhas lógicas corretas; `§ 4o`/`§ 2°` → `§ 4º`/`§ 2º` (A8).

## Fase 3 — Parser (perfil `cp`)
- [ ] `perfil.py` + `perfis/cp.toml`
- [ ] `parser.py`: hierarquia, dispositivos, rubricas, penas (RF07–RF11)

**Saída:** A1–A8 (exceto o que depende de vigência) e A13 com a base real do CP.

## Fase 4 — Notas, vigência e relatório
- [ ] `notas.py` (§7.3), `vigencia.py` (D1, RF14–RF16), `validador.py` (V1–V7)
- [ ] Relatório JSON + Markdown

**Saída:** A1–A8 completos; snapshot de regressão do CP criado.

## Fase 5 — PDF
- [ ] `fontes/pdf.py`, `segmentador.py`, perfis `nscgj` e `lei_sp`

**Saída:** A9–A12.

## Fase 6 — URL com cache
- [ ] Download + cache com data e SHA-256 (RF02)

**Saída:** A14.

## Fase 7 — CLI
- [ ] `extrair` e `recortar` ligados ao pipeline; códigos de saída

**Saída:** comandos do PRD §10 rodam ponta a ponta.
