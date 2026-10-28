# Pendências

Lista única e ordenada do que falta. A ordem é a prioridade sugerida; o dono do projeto pode
escolher outro item. O *como* fica na spec citada, não aqui. O estado real se confere no git e no
código. O número de um item nunca muda; o novo pega o próximo livre.

As fases de implementação (sequência do PRD §14) são os itens 1, 6 a 11 abaixo, e as pendências e
riscos de requisito (P1–P7) seguem no PRD §12, de onde este arquivo só aponta.

## Agora

- **Em curso:** nada. A fase 0 (setup) está fechada.
- **Próximo sugerido:** item 1 (modelo, ordenação e recorte), pelo `/spec` se passar de
  um commit.

## Fila

- [ ] **1. Fase 1: modelo, ordenação e recorte.** `modelo.py`, `chave_ordenacao()`,
      `recorte.py`. Aceite: A13 com base sintética. `/spec`.
- [ ] **2. Fontes brutas no repositório (T1).** A1 e o snapshot precisam do `.mht` do CP e de PDF.
      Versionar em `tests/fixtures/` se o tamanho for aceitável; senão, o teste `regressao` pula
      quando o arquivo não existe. Decidir antes da fase 3.
- [ ] **3. Formato do relatório (T2).** Gerar `base.relatorio.json` e `base.relatorio.md`
      (proposta da antiga spec técnica). Confirmar com o PRD RF17 e P4 antes da fase 4.
- [ ] **4. Confirmar P1 e P2 do PRD §12.** Artigo avulso inclui só ele (assumido); recorte
      sub-artigo (`196, inciso XX`) fica fora da Etapa 1. Confirmar antes da fase 1 fechar o `recorte`.
- [ ] **5. Ponto de atenção P3 (regra temporal do edital).** Número e ano de cada nota ficam na
      base; conferência de data contra o corte é da Etapa 2 ou lista manual no perfil. Decidir na
      fase 4.
- [ ] **6. Fase 2: leitor HTML + normalizador.** `fontes/html.py` (`.mht` e arquivo local; RF03, RF04;
      H1–H4) e `normalizador.py` (ordinais, travessões; H11, H13). Aceite: trecho do art. 121 vira
      linhas lógicas corretas; `§ 4o`/`§ 2°` → `§ 4º`/`§ 2º` (A8).
- [ ] **7. Fase 3: parser (perfil `cp`).** `perfil.py`, `perfis/cp.toml`, `parser.py` (hierarquia,
      dispositivos, rubricas, penas; RF07–RF11). Aceite: A1–A8 (exceto vigência) e A13 com a base real
      do CP.
- [ ] **8. Fase 4: notas, vigência e relatório.** `notas.py` (§7.3), `vigencia.py` (D1, RF14–RF16),
      `validador.py` (V1–V7), relatório JSON + Markdown. Aceite: A1–A8 completos; snapshot de
      regressão do CP criado.
- [ ] **9. Fase 5: PDF.** `fontes/pdf.py`, `segmentador.py`, perfis `nscgj` e `lei_sp`. Aceite: A9–A12.
- [ ] **10. Fase 6: URL com cache.** Download + cache com data e SHA-256 (RF02). Aceite: A14.
- [ ] **11. Fase 7: CLI.** `extrair` e `recortar` ligados ao pipeline, com códigos de saída. Aceite:
      comandos do PRD §10 rodam ponta a ponta.

## Concluídos recentes

Os últimos cinco, mais novo primeiro; o histórico completo é o `git log`.

- ~~**0. Setup do projeto (fase 0)**~~ — 2026-10-26, `f088e51`
