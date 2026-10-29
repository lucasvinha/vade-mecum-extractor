# Pendências

Lista única e ordenada do que falta. A ordem é a prioridade sugerida; o dono do projeto pode
escolher outro item. O *como* fica no ADR ou na spec citada, não aqui. O estado real se confere
no git e no código. O número de um item nunca muda; o novo pega o próximo livre.

A sequência de implementação são os itens 1 e 6 a 11, nesta ordem: cada um parte do anterior.
As pendências e riscos de requisito (P1–P7) estão nos itens 4 e 5 e em "Riscos acompanhados".

## Agora

- **Em curso:** nada.
- **Próximo sugerido:** item 1 (modelo, ordenação e recorte), pelo `/spec` se passar de
  um commit.

## Fila

- [ ] **1. Fase 1: modelo, ordenação e recorte.** `modelo.py`, `chave_ordenacao()`,
      `recorte.py`. Aceite: A13 com base sintética. `/spec`.
- [ ] **2. Fontes brutas no repositório.** A1 e o snapshot precisam do `.mht` do CP e de PDF.
      Versionar em `tests/fixtures/` se o tamanho for aceitável (texto legal é público); senão,
      o teste `regressao` pula quando o arquivo não existe. Decidir antes da fase 3.
- [ ] **3. Formato do relatório.** Gerar `base.relatorio.json` (consumo pela Etapa 2) e
      `base.relatorio.md` (leitura). RF17 aceita qualquer um; P4 pede JSON estruturado.
      Confirmar antes da fase 4.
- [ ] **4. Confirmar P1 e P2.** **P1:** artigo avulso (`121`) inclui só ele ou também `121-X`?
      ADR-004 cobre só faixas; assumido **só ele** ([negocio/recorte-e-cli.md](negocio/recorte-e-cli.md)).
      **P2:** recorte sub-artigo (`196, inciso XX`; `282, § 1º`), que o edital usa na NSCGJ; na
      Etapa 1 entra o artigo inteiro; avaliar suporte a `art.inciso` na sintaxe. Confirmar antes
      da fase 1 fechar o `recorte`.
- [ ] **5. Ponto de atenção P3 (regra temporal do edital).** Vigência até 19/10/2026 × captura do
      HTML em 26/10/2026: há alterações "de 2026" no CP (Leis 15.358, 15.384, 15.402, 15.425) e
      as notas trazem só o ano. Número e ano de cada nota ficam na base; a conferência de data
      contra o corte é da Etapa 2 ou lista manual de leis posteriores ao corte no perfil.
      Decidir na fase 4.
- [ ] **6. Fase 2: leitor HTML + normalizador.** `fontes/html.py` (`.mht` e arquivo local; RF03, RF04;
      H1–H4) e `normalizador.py` (ordinais, travessões; H11, H13). Aceite: trecho do art. 121 vira
      linhas lógicas corretas; `§ 4o`/`§ 2°` → `§ 4º`/`§ 2º` (A8).
- [ ] **7. Fase 3: parser (perfil `cp`).** `perfil.py`, `perfis/cp.toml`, `parser.py` (hierarquia,
      dispositivos, rubricas, penas; RF07–RF11). Aceite: A1–A8 (exceto vigência) e A13 com a base real
      do CP.
- [ ] **8. Fase 4: notas, vigência e relatório.** `notas.py` ([negocio/vigencia-e-notas.md](negocio/vigencia-e-notas.md)),
      `vigencia.py` (ADR-001, RF14–RF16), `validador.py` (V1–V7), relatório JSON + Markdown.
      Aceite: A1–A8 completos; snapshot de regressão do CP criado.
- [ ] **9. Fase 5: PDF.** `fontes/pdf.py`, `segmentador.py`, perfis `nscgj` e `lei_sp`. Aceite: A9–A12.
- [ ] **10. Fase 6: URL com cache.** Download + cache com data e SHA-256 (RF02). Aceite: A14.
- [ ] **11. Fase 7: CLI.** `extrair` e `recortar` ligados ao pipeline, com códigos de saída. Aceite:
      comandos de [negocio/recorte-e-cli.md](negocio/recorte-e-cli.md) rodam ponta a ponta.

## Riscos acompanhados

Não são itens de trabalho: cada um é tratado pelo item citado.

- **P4 — perda do "revogado/deslocado" ao descartar (ADR-001).** O relatório guarda os
  descartes de forma estruturada (JSON), para a Etapa 2 consultar. Item 3.
- **P5 — rubrica no PDF** (sem rubricas na amostra atual; normas penais em PDF terão).
  Heurística em [negocio/parsing.md](negocio/parsing.md); validar quando houver PDF de norma
  penal. Item 9.
- **P6 — mudança de layout do Planalto.** O snapshot de regressão detecta a quebra; o leitor
  depende só de negrito e alinhamento. Item 8.
- **P7 — PDFs de outras origens** (Senado, editoras). O leitor PDF expõe colunas, zonas de
  cabeçalho e rodapé e mapa de fontes no perfil. Item 9.

## Concluídos recentes

Os últimos cinco, mais novo primeiro; o histórico completo é o `git log`.

- ~~**12. Estrutura da documentação**~~ — 2026-10-28, fechado pelo commit que apagou a spec
- ~~**0. Setup do projeto (fase 0)**~~ — 2026-10-26, `f088e51`
