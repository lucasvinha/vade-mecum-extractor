# Pendências

Lista única e ordenada do que falta. A ordem é a prioridade sugerida; o dono do projeto pode
escolher outro item. O *como* fica no ADR ou na spec citada, não aqui. O estado real se confere
no git e no código. O número de um item nunca muda; o novo pega o próximo livre.

A implementação segue os **marcos** M1–M9, nesta ordem: cada um parte do anterior. Marco é um
item grande da fila e vira uma spec (`/spec <item>`), fatiada em fases de um commit (`/fase`).
O número do marco acompanha a ordem; o do item, não. Das pendências de requisito, P1 e P2 foram
confirmadas, P3 está no item 5 e P4–P7 em "Riscos acompanhados".

## Agora

- **Em curso:** M3 (item 7), pela spec `docs/processo/specs/m3-parser-cp.md`.
- **Próximo sugerido:** M4 (item 8), pelo `/spec`, quando o M3 fechar.
- **Meta:** a base do CP no M4 e as normas do edital que estão no Planalto no M6. Prova em
  14/03/2027. Do Planalto: CP, CPP, CPC, CC, LINDB, CF e Leis 9.099, 8.429, 6.830 e 13.146. Fora
  dele, no M8: NSCGJ, Leis SP 10.261 e 11.608 e Res. CNJ 354. Os artigos de cada tópico estão em
  [claude/topicos-oj2026.json](../claude/topicos-oj2026.json).

## Fila

- [ ] **M3 · 7. Parser (perfil `cp`) + `extrair`.** `perfil.py`, `perfis/cp.toml`, `notas.py`
      ([negocio/vigencia-e-notas.md](negocio/vigencia-e-notas.md)), `parser.py` (hierarquia,
      dispositivos, rubricas, penas; RF07–RF11) e o subcomando `extrair`, que já grava o
      relatório, com código de saída 2 para erro de entrada. Aceite: A1–A8, exceto vigência.
      `notas.py` veio do M4 (2026-11-01): sem ele o parser não separa nota de texto.
- [ ] **M4 · 8. Vigência e validação.** `vigencia.py` (ADR-001, RF14–RF16), `validador.py`
      (V1–V7) e o motivo estruturado do descarte no relatório. Aceite: A1–A8 completos;
      snapshot dos enxertos do CP. **Entrega a primeira base usável: o CP.**
- [ ] **M5 · 15. Recorte + `recortar`.** `recorte.py` e o subcomando (RF18, ADR-004, P1, P2).
      Aceite: A13. Em 2026-10-31 o operador decidiu: o Python recorta e o Claude recebe só o
      recorte (RF18 e ADR-003 mantidos). Nas cinco normas maiores, o edital cobra 686 dos 4.540
      artigos da numeração-base, uns 15%. Casos reais do `arts` dos tópicos: ordinal (`1º a 12`,
      `8º; 9º`), milhar (`1.169 a 1.173`) e letra (`396-A`, `798-A`). A conferir na spec: se a
      entrada sai do `arts` e o §6 de [recorte-e-cli.md](negocio/recorte-e-cli.md) (2026-10-29).
- [ ] **M6 · 13. Perfis das normas do Planalto.** `cpp`, `cpc`, `cc` (com a LINDB, DL 4.657),
      `cf` e as Leis 9.099, 8.429, 6.830 e 13.146. Um perfil por fase, cada um com casos de
      aceite novos e enxerto real. A conferir na spec: milhar no HTML (`Art. 1.072`, P13), a CF
      com o ADCT na mesma página (a numeração recomeça), normas sem rubrica e sem pena, e se as
      leis menores cabem no perfil `padrao` (ADR-002).
- [ ] **M7 · 10. URL com cache.** Download + cache com data e SHA-256 (RF02). Aceite: A14.
      Opcional: o `.mht` salvo à mão já cobre as normas do Planalto. O Planalto recusa cliente
      sem User-Agent de navegador (visto no M2, 2026-10-31): a spec decide o cabeçalho.
- [ ] **M8 · 9. PDF.** `fontes/pdf.py`, `segmentador.py`, perfis `nscgj` e `lei_sp`. Aceite:
      A9–A12. NSCGJ e Lei SP 10.261 vêm em PDF, com o recorte trazido pelo operador
      (2026-10-31). Lei SP 11.608 e Res. CNJ 354 também não estão no Planalto e já estão no PDF
      analisado (P5 de [negocio/fontes.md](negocio/fontes.md)); origem a confirmar. O leitor é
      também pré-requisito do M9.
- [ ] **M9 · 14. Extrator de questões.** PDF de cursinho (questão, alternativas, gabarito embaixo
      ou em anexo) → `questoes-oj/1` ([schema-questoes-json.md](schema-questoes-json.md)).
      Fixture: enxerto de duas páginas. Antes da spec: ADR de escopo (subpacote neste repositório
      ou repositório próprio).

## Perguntas em aberto

- [ ] **5. Ponto de atenção P3 (regra temporal do edital).** Vigência até 19/10/2026 × captura do
      HTML em 26/10/2026: há alterações "de 2026" no CP (Leis 15.358, 15.384, 15.402, 15.425) e
      as notas trazem só o ano. Número e ano de cada nota ficam na base; a conferência de data
      contra o corte é da Etapa 2 ou lista manual de leis posteriores ao corte no perfil.
      Decidir no M4.
- [ ] **18. H8: tachado só pelo CSS.** Achado na fase 4 do M2 (2026-10-31). A H8 lista
      `<strike>`, `<s>` e `<del>`, mas 55 tachados vêm por `text-decoration: line-through` no
      `style`, sem tag: 35 no CPC, 16 na Lei 8.429 (art. 12, IV antigo) e 4 na Lei 13.146. O
      leitor deixa essa redação como vigente (ADR-001). Na Lei 8.429, art. 17, § 3º, o `<strike>`
      fecha antes do `)` da nota, tachado por CSS, e a linha inteira vira `aviso` em vez de
      `descarte`. A decidir pelo operador: o CSS conta como tachado (fase 4b, como a 3b)?

## Riscos acompanhados

Não são itens de trabalho: cada um é tratado pelo item citado.

- **P4 — perda do "revogado/deslocado" ao descartar (ADR-001).** O relatório JSON guarda os
  descartes de forma estruturada, para a Etapa 2 consultar. Item 8.
- **P5 — rubrica no PDF** (sem rubricas na amostra atual; normas penais em PDF terão).
  Heurística em [negocio/parsing.md](negocio/parsing.md); validar quando houver PDF de norma
  penal. Item 9.
- **P6 — mudança de layout do Planalto.** O leitor depende só de negrito, alinhamento e tachado (H8). O
  snapshot é dos enxertos e não vê a página nova: a quebra aparece nos avisos do validador e no
  antes e depois local do `/regressao`. Item 8.
- **P7 — PDFs de outras origens** (Senado, editoras). O leitor PDF expõe colunas, zonas de
  cabeçalho e rodapé e mapa de fontes no perfil. Item 9.

## Concluídos recentes

Os últimos cinco, mais novo primeiro; o histórico completo é o `git log`.

- ~~**16. RF19 × esquema por tipo**~~ — 2026-11-01: `origem` fica na memória e no relatório,
  fora do JSON da base
- ~~**M2 · 6. Leitor HTML + normalizador**~~ — 2026-10-31, `ba7c3bd`: `ler_html` (`.mht` e
  `.htm` locais → `FonteLida`, tachado pela H8) e `normalizar`; aceite A8
- ~~**17. H6: negrito que o leitor HTML não vê**~~ — 2026-10-31, `c2cc27e`: `html5lib` e peso
  pelo `font-weight`
- ~~**M1 · 1. Modelo e ordenação**~~ — 2026-10-31, `a5dd794`: `modelo.py` com esquema estável
  por tipo
- ~~**2. Fontes brutas no repositório**~~ — 2026-10-30, `04564d1`: só enxertos; fonte inteira e
  extrações em `dados/`
