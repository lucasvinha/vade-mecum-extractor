# Pendências

Lista única e ordenada do que falta. A ordem é a prioridade sugerida; o dono do projeto pode
escolher outro item. O *como* fica no ADR ou na spec citada, não aqui. O estado real se confere
no git e no código. O número de um item nunca muda; o novo pega o próximo livre.

A implementação segue os **marcos** M1–M10, nesta ordem: cada um parte do anterior. Marco é um
item grande da fila e vira uma spec (`/spec <item>`), fatiada em fases de um commit (`/fase`).
O número do marco acompanha a ordem; o do item, não. Das pendências de requisito, P1 e P2 foram
confirmadas, P3 foi decidida no M4 (pergunta 5) e P4–P7 estão em "Riscos acompanhados".

## Agora

- **Em curso:** nenhum marco; o M6 fechou em 2026-11-02 e o vade mecum de Direito Penal já sai
  pelas três etapas (ADR-005).
- **Próximo sugerido:** M7 (item 13), pelo `/spec`. Cada perfil novo destrava a matéria da norma
  no `/vade-mecum`.
- **Meta:** a base do CP no M4 e as normas do edital que estão no Planalto no M7. Prova em
  14/03/2027. Do Planalto: CP, CPP, CPC, CC, LINDB, CF e Leis 9.099, 8.429, 6.830 e 13.146. Fora
  dele, no M9: NSCGJ, Leis SP 10.261 e 11.608 e Res. CNJ 354. Os artigos de cada tópico estão em
  [claude/topicos-oj2026.json](../claude/topicos-oj2026.json).

## Fila

- [ ] **M7 · 13. Perfis das normas do Planalto.** `cpp`, `cpc`, `cc` (com a LINDB, DL 4.657),
      `cf` e as Leis 9.099, 8.429, 6.830 e 13.146. Um perfil por fase, cada um com casos de
      aceite novos e enxerto real. A conferir na spec: milhar no HTML (`Art. 1.072`, P13), a CF
      com o ADCT na mesma página (a numeração recomeça), normas sem rubrica e sem pena, e se as
      leis menores cabem no perfil `padrao` (ADR-002). Do M3: rubrica antes do primeiro
      nível ou artigo cai no `preambulo` (H17), e cabeçalho sem tipo de norma deixa
      `norma.titulo` vazio, com `aviso`. Do M6: lei sem perfil próprio sai com `norma.id` igual
      a `padrao`, que não casa com a `norma` dos tópicos (`lei9099`); a spec decide se cada lei
      ganha perfil, mesmo mínimo, ou se o id vem de outro lugar. A base nova entra em
      `dados/bases/<norma>/`, gerada de um `.mht` (o teste de sincronia não aceita `.htm`).
- [ ] **M8 · 10. URL com cache.** Download + cache com data e SHA-256 (RF02). Aceite: A14.
      Opcional: o `.mht` salvo à mão já cobre as normas do Planalto. O Planalto recusa cliente
      sem User-Agent de navegador (visto no M2, 2026-10-31): a spec decide o cabeçalho.
- [ ] **M9 · 9. PDF.** `fontes/pdf.py`, `segmentador.py`, perfis `nscgj` e `lei_sp`. Aceite:
      A9–A12. NSCGJ e Lei SP 10.261 vêm em PDF, com o recorte trazido pelo operador
      (2026-10-31). Lei SP 11.608 e Res. CNJ 354 também não estão no Planalto e já estão no PDF
      analisado (P5 de [negocio/fontes.md](negocio/fontes.md)); origem a confirmar. O leitor é
      também pré-requisito do M10.
- [ ] **M10 · 14. Extrator de questões.** PDF de cursinho (questão, alternativas, gabarito embaixo
      ou em anexo) → `questoes-oj/1` ([schema-questoes-json.md](schema-questoes-json.md)).
      Fixture: enxerto de duas páginas. Antes da spec: ADR de escopo (subpacote neste repositório
      ou repositório próprio).

## Perguntas em aberto

Nenhuma. As 4 leis "de 2026" no CP (15.358, 15.384, 15.402, 15.425) não bloqueiam marco nenhum:
quem confere contra o corte está em [negocio/vigencia-e-notas §4](negocio/vigencia-e-notas.md).

## Riscos acompanhados

Não são itens de trabalho: cada um é tratado pelo item citado.

- **P4 — perda do "revogado/deslocado" ao descartar (ADR-001).** O relatório JSON guarda os
  descartes de forma estruturada (RF16: `id`, `rotulo`, `rubrica`, `motivo`, `notas`), para a
  Etapa 3 consultar; o destino do dispositivo deslocado não é extraído. Coberto no M4.
- **P5 — rubrica no PDF** (sem rubricas na amostra atual; normas penais em PDF terão).
  Heurística em [negocio/parsing.md](negocio/parsing.md); validar quando houver PDF de norma
  penal. Item 9.
- **P6 — mudança de layout do Planalto.** O leitor depende só de negrito, alinhamento e tachado (H8). O
  snapshot é dos enxertos e não vê a página nova: a quebra aparece nos avisos V1–V6 do validador
  e no antes e depois local do `/regressao`. Coberto no M4.
- **P7 — PDFs de outras origens** (Senado, editoras). O leitor PDF expõe colunas, zonas de
  cabeçalho e rodapé e mapa de fontes no perfil. Item 9.

## Concluídos recentes

Os últimos cinco, mais novo primeiro; o histórico completo é o `git log`.

- ~~**M6 · 19. Vade mecum em 3 etapas**~~ — 2026-11-02, `4d7d32f`: ADR-005, `dados/`
  versionado com teste de sincronia, tópicos `topicos-oj/2`, `recortar --topicos --materia`,
  `conferir` (negocio/vade-mecum), instruções da Etapa 3 e a skill `/vade-mecum`; piloto
  `dados/vade-mecum/oj26/penal.html` e `.pdf`, aprovado pelo operador
- ~~**M5 · 15. Recorte + `recortar`**~~ — 2026-11-02, `a57499b`: `recorte.py` (`interpretar`,
  `recortar`), `de_json` e o subcomando `recortar`, com relatório próprio que copia os descartes
  da base; aceite A13. A CLI não lê o MD nem os tópicos do edital (negocio/recorte-e-cli)
- ~~**M4 · 8. Vigência e validação**~~ — 2026-11-01, `d803051`: `vigencia.py`
  (`filtrar_vigentes`), `validador.py` (V1–V6) e o `descarte` estruturado do RF16; aceite A1–A8
  e snapshot dos enxertos. No CP, o único aviso V* é a V4 do art. 272 (H20). A nota de nível
  segue `aviso` de texto livre (H18)
- ~~**5. P3: regra temporal do edital**~~ — 2026-11-01, `d803051`: a base guarda norma e ano de
  cada nota, e a conferência contra o corte é da Etapa 3 (negocio/vigencia-e-notas)
- ~~**M3 · 7. Parser (perfil `cp`) + `extrair`**~~ — 2026-11-01, `cc3d6fd`: `perfil.py`,
  `notas.py`, `parser.py` (`analisar` → `Analise`) e `extrair`; aceite A1–A4, A6 e A7
  estruturais, sem linha não classificada no CP
